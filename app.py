"""
F1 25 Telemetry Dashboard - Broadcast Engineer Display
Flask + Socket.IO per streaming dati in tempo reale
Layout ispirato al broadcast TV F1
"""

import os
import sys
import ctypes

import socket

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import threading
import time
from collections import deque

from analyzer_Packets import telemetry_data, listener
from maps import *
from track_loader import load_track, get_track_json, dist_to_position, preload_all_tracks, TRACK_FILE_MAP

import webbrowser
import tkinter as tk
from tkinter import font
import qrcode
from PIL import Image, ImageTk

app = Flask(__name__)
app.config['SECRET_KEY'] = 'f1-telemetry-secret-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

udp_thread = None

# === BEST SECTOR TRACKING ===
best_sectors = {'s1': 0, 's2': 0, 's3': 0}
best_lap_ms = 0
last_sector_values = {'s1_prev': 0, 's2_prev': 0, 'last_s3': 0}

# === PER-CAR FASTEST LAP TRACKING ===
car_fastest_laps = {}  # {car_index: fastest_lap_ms}
overall_fastest_lap = {'time_ms': 0, 'car_index': -1}

# === PER-CAR SECTOR TRACKING ===
car_best_sectors = {}     # {car_index: {'s1': 0, 's2': 0, 's3': 0}}
car_last_sector_vals = {} # {car_index: {'s1_prev': 0, 's2_prev': 0, 'last_lap_prev': 0}}
overall_best_sectors = {'s1': 0, 's2': 0, 's3': 0}

# === TELEMETRY TRACE HISTORY ===
TRACE_MAX_LEN = 200  # ~6.6 seconds at 30Hz
throttle_trace = deque(maxlen=TRACE_MAX_LEN)
brake_trace = deque(maxlen=TRACE_MAX_LEN)
speed_trace = deque(maxlen=TRACE_MAX_LEN)


# ========================== UTILITY ==========================

def format_time_ms(ms):
    """Formatta millisecondi in M:SS.mmm"""
    if ms <= 0:
        return "0:00.000"
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{minutes}:{seconds:02d}.{millis:03d}"


def format_delta(ms):
    """Formatta delta tempo con segno"""
    if ms == 0:
        return "+0.000"
    sign = "+" if ms > 0 else ""
    seconds = abs(ms) / 1000
    return f"{sign}{seconds:.3f}"


def calculate_delta_behind(player_idx):
    """Calcola il delta rispetto alla macchina dietro"""
    try:
        player_pos = telemetry_data.lap_data[player_idx].car_position
        if player_pos <= 0:
            return "+0.000"
        for i in range(22):
            if telemetry_data.lap_data[i].car_position == player_pos + 1:
                delta_ms = -telemetry_data.lap_data[i].delta_to_car_in_front_ms
                return format_delta(delta_ms)
        return "+0.000"
    except Exception:
        return "+0.000"


def _compute_sector3(lap):
    """Sector 3 = last_lap - s1(last) - s2(last)"""
    if not lap:
        return 0
    if lap.last_lap_time_ms > 0 and last_sector_values['last_s3'] > 0:
        return last_sector_values['last_s3']
    return 0


def _update_best_sectors(player_idx):
    """Aggiorna i migliori settori e lap time"""
    global best_sectors, best_lap_ms, last_sector_values
    try:
        lap = telemetry_data.lap_data[player_idx]
        s1 = lap.sector1_time_ms
        s2 = lap.sector2_time_ms

        if s1 > 0:
            if best_sectors['s1'] == 0 or s1 < best_sectors['s1']:
                best_sectors['s1'] = s1
        if s2 > 0:
            if best_sectors['s2'] == 0 or s2 < best_sectors['s2']:
                best_sectors['s2'] = s2

        last_lap = lap.last_lap_time_ms
        if last_lap > 0:
            stored_s1 = last_sector_values.get('s1_prev', 0)
            stored_s2 = last_sector_values.get('s2_prev', 0)
            if stored_s1 > 0 and stored_s2 > 0:
                s3 = last_lap - stored_s1 - stored_s2
                if s3 > 0:
                    last_sector_values['last_s3'] = s3
                    if best_sectors['s3'] == 0 or s3 < best_sectors['s3']:
                        best_sectors['s3'] = s3

            if best_lap_ms == 0 or last_lap < best_lap_ms:
                if lap.current_lap_invalid == 0:
                    best_lap_ms = last_lap

        if s1 > 0:
            last_sector_values['s1_prev'] = s1
        if s2 > 0:
            last_sector_values['s2_prev'] = s2
    except Exception:
        pass


def _update_all_car_sectors():
    """Aggiorna i migliori settori per ogni auto in pista"""
    global car_best_sectors, car_last_sector_vals, overall_best_sectors
    try:
        for i in range(22):
            lap = telemetry_data.lap_data[i]
            if telemetry_data.participants[i].name == 'Unknown':
                continue
            if i not in car_best_sectors:
                car_best_sectors[i] = {'s1': 0, 's2': 0, 's3': 0}
                car_last_sector_vals[i] = {'s1_prev': 0, 's2_prev': 0, 'last_lap_prev': 0}

            vals = car_last_sector_vals[i]
            best = car_best_sectors[i]

            s1 = lap.sector1_time_ms
            s2 = lap.sector2_time_ms
            last_lap = lap.last_lap_time_ms

            if s1 > 0:
                if best['s1'] == 0 or s1 < best['s1']:
                    best['s1'] = s1
                if overall_best_sectors['s1'] == 0 or best['s1'] < overall_best_sectors['s1']:
                    overall_best_sectors['s1'] = best['s1']

            if s2 > 0:
                if best['s2'] == 0 or s2 < best['s2']:
                    best['s2'] = s2
                if overall_best_sectors['s2'] == 0 or best['s2'] < overall_best_sectors['s2']:
                    overall_best_sectors['s2'] = best['s2']

            # Quando completa un giro, calcola S3 = last_lap - s1_prev - s2_prev
            if last_lap > 0 and last_lap != vals['last_lap_prev']:
                s1_used = vals['s1_prev']
                s2_used = vals['s2_prev']
                if s1_used > 0 and s2_used > 0:
                    s3 = last_lap - s1_used - s2_used
                    if s3 > 0:
                        if best['s3'] == 0 or s3 < best['s3']:
                            best['s3'] = s3
                        if overall_best_sectors['s3'] == 0 or best['s3'] < overall_best_sectors['s3']:
                            overall_best_sectors['s3'] = best['s3']
                vals['last_lap_prev'] = last_lap

            if s1 > 0:
                vals['s1_prev'] = s1
            if s2 > 0:
                vals['s2_prev'] = s2
    except Exception:
        pass


def _update_car_fastest_laps():
    """Aggiorna il fastest lap per ogni auto"""
    global car_fastest_laps, overall_fastest_lap
    try:
        for i in range(22):
            lap = telemetry_data.lap_data[i]
            if lap.last_lap_time_ms > 0 and telemetry_data.participants[i].name != 'Unknown':
                if i not in car_fastest_laps or lap.last_lap_time_ms < car_fastest_laps[i]:
                    car_fastest_laps[i] = lap.last_lap_time_ms
                if overall_fastest_lap['time_ms'] == 0 or lap.last_lap_time_ms < overall_fastest_lap['time_ms']:
                    overall_fastest_lap['time_ms'] = lap.last_lap_time_ms
                    overall_fastest_lap['car_index'] = i
    except Exception:
        pass


def _update_trace(player_idx):
    """Aggiorna i buffer dei tracciati telemetrici"""
    try:
        telemetry = telemetry_data.car_telemetry[player_idx]
        throttle_trace.append(int(telemetry.throttle * 100))
        brake_trace.append(int(telemetry.brake * 100))
        speed_trace.append(telemetry.speed)
    except Exception:
        throttle_trace.append(0)
        brake_trace.append(0)
        speed_trace.append(0)


# ========================== DATA BUILDERS ==========================

def get_player_telemetry():
    """Estrae e formatta tutti i dati del giocatore per il dashboard broadcast"""
    try:
        player_idx = telemetry_data.player_car_index
        if player_idx < 0 or player_idx >= 22:
            return None

        player_data = telemetry_data.get_player_data()
        if not player_data:
            return None

        motion = player_data.get('motion')
        lap = player_data.get('lap')
        telemetry = player_data.get('telemetry')
        status = player_data.get('status')
        damage = player_data.get('damage')
        participant = player_data.get('participant')
        session = telemetry_data.session

        data = {
            # === SESSION ===
            'session_time': round(telemetry_data.session_time, 1),
            'session_type': SESSION_TYPE_MAP.get(session.session_type, 'Unknown'),
            'track': TRACK_IDS_MAP.get(session.track_id, 'Unknown'),
            'track_id': session.track_id,
            'weather': WEATHER_MAP.get(session.weather, 'Unknown'),
            'weather_emoji': WEATHER_EMOJI.get(session.weather, '☀️'),
            'track_temp': session.track_temperature,
            'air_temp': session.air_temperature,
            'total_laps': session.total_laps,
            'session_time_left': session.session_time_left,
            'safety_car': SAFETY_CAR_MAP.get(session.safety_car_status, 'None'),
            'safety_car_status': session.safety_car_status,
            'pit_speed_limit': session.pit_speed_limit,
            'formula': FORMULA_MAP.get(session.formula, 'F1'),

            # === PLAYER INFO ===
            'player_name': participant.name if participant else 'Player',
            'player_team': TEAM_IDS_MAP.get(participant.team_id, 'Unknown') if participant else 'Unknown',
            'player_team_id': participant.team_id if participant else 0,
            'race_number': participant.race_number if participant else 0,

            # === LAP DATA ===
            'current_lap': lap.current_lap_num if lap else 0,
            'position': lap.car_position if lap else 0,
            'current_lap_time': format_time_ms(lap.current_lap_time_ms) if lap else "0:00.000",
            'current_lap_time_raw': lap.current_lap_time_ms if lap else 0,
            'last_lap_time': format_time_ms(lap.last_lap_time_ms) if lap else "0:00.000",
            'last_lap_time_raw': lap.last_lap_time_ms if lap else 0,
            'sector1_time': lap.sector1_time_ms if lap else 0,
            'sector2_time': lap.sector2_time_ms if lap else 0,
            'sector3_time': _compute_sector3(lap),
            'current_sector': lap.sector + 1 if lap else 0,
            'best_sector1': best_sectors['s1'],
            'best_sector2': best_sectors['s2'],
            'best_sector3': best_sectors['s3'],
            'best_lap_time': format_time_ms(best_lap_ms) if best_lap_ms > 0 else '--',
            'best_lap_time_raw': best_lap_ms,
            'lap_distance': round(lap.lap_distance, 0) if lap else 0,
            'total_distance': round(lap.total_distance, 0) if lap else 0,
            'track_length': session.track_length,
            'lap_invalid': lap.current_lap_invalid if lap else 0,
            'grid_position': lap.grid_position if lap else 0,

            # === DELTAS ===
            'delta_leader': format_delta(lap.delta_to_leader_ms) if lap else "+0.000",
            'delta_ahead': format_delta(lap.delta_to_car_in_front_ms) if lap else "+0.000",
            'delta_behind': calculate_delta_behind(player_idx),

            # === TELEMETRY ===
            'speed': telemetry.speed if telemetry else 0,
            'gear': telemetry.gear if telemetry else 0,
            'rpm': telemetry.engine_rpm if telemetry else 0,
            'max_rpm': status.max_rpm if status else 15000,
            'throttle': int(telemetry.throttle * 100) if telemetry else 0,
            'brake': int(telemetry.brake * 100) if telemetry else 0,
            'steer': round(telemetry.steer * 100, 1) if telemetry else 0,
            'clutch': telemetry.clutch if telemetry else 0,
            'rev_lights_percent': telemetry.rev_lights_percent if telemetry else 0,
            'drs': telemetry.drs if telemetry else 0,
            'drs_allowed': status.drs_allowed if status else 0,

            # === FUEL ===
            'fuel': round(status.fuel_in_tank, 1) if status else 0,
            'fuel_capacity': round(status.fuel_capacity, 2) if status else 0,
            'fuel_remaining_laps': round(status.fuel_remaining_laps, 2) if status else 0,
            'fuel_mix': FUEL_MIX_MAP.get(status.fuel_mix, 'Standard') if status else 'Standard',

            # === ERS ===
            'ers_mode': ERS_DEPLOY_MODE_MAP.get(status.ers_deploy_mode, 'None') if status else 'None',
            'ers_deploy_mode_raw': status.ers_deploy_mode if status else 0,
            'ers_store': round(status.ers_store_energy / 4000000 * 100, 1) if status else 0,

            # === SETUP ===
            'brake_bias': status.front_brake_bias if status else 50,
            'traction_control': TRACTION_CONTROL_MAP.get(status.traction_control, 'Off') if status else 'Off',
            'anti_lock_brakes': 'ON' if (status and status.anti_lock_brakes == 1) else 'OFF',

            # === TYRES ===
            'tyre_compound': VISUAL_TYRE_MAP.get(status.visual_tyre_compound, '-') if status else '-',
            'tyre_actual': ACTUAL_TYRE_COMPOUND_MAP.get(status.actual_tyre_compound, '-') if status else '-',
            'tyre_age': status.tyres_age_laps if status else 0,
            'tyre_wear_rl': round(damage.tyres_wear[0], 1) if damage else 0,
            'tyre_wear_rr': round(damage.tyres_wear[1], 1) if damage else 0,
            'tyre_wear_fl': round(damage.tyres_wear[2], 1) if damage else 0,
            'tyre_wear_fr': round(damage.tyres_wear[3], 1) if damage else 0,
            'tyre_temp_rl': telemetry.tyres_surface_temperature[0] if telemetry else 0,
            'tyre_temp_rr': telemetry.tyres_surface_temperature[1] if telemetry else 0,
            'tyre_temp_fl': telemetry.tyres_surface_temperature[2] if telemetry else 0,
            'tyre_temp_fr': telemetry.tyres_surface_temperature[3] if telemetry else 0,
            'tyre_inner_rl': telemetry.tyres_inner_temperature[0] if telemetry else 0,
            'tyre_inner_rr': telemetry.tyres_inner_temperature[1] if telemetry else 0,
            'tyre_inner_fl': telemetry.tyres_inner_temperature[2] if telemetry else 0,
            'tyre_inner_fr': telemetry.tyres_inner_temperature[3] if telemetry else 0,

            # === BRAKES ===
            'brake_temp_rl': telemetry.brakes_temperature[0] if telemetry else 0,
            'brake_temp_rr': telemetry.brakes_temperature[1] if telemetry else 0,
            'brake_temp_fl': telemetry.brakes_temperature[2] if telemetry else 0,
            'brake_temp_fr': telemetry.brakes_temperature[3] if telemetry else 0,
            'engine_temp': telemetry.engine_temperature if telemetry else 0,

            # === DAMAGE ===
            'damage_front_left': damage.front_left_wing_damage if damage else 0,
            'damage_front_right': damage.front_right_wing_damage if damage else 0,
            'damage_rear': damage.rear_wing_damage if damage else 0,
            'damage_floor': damage.floor_damage if damage else 0,
            'damage_gearbox': damage.gearbox_damage if damage else 0,
            'damage_engine': damage.engine_damage if damage else 0,
            'drs_fault': damage.drs_fault if damage else 0,
            'ers_fault': damage.ers_fault if damage else 0,
            'engine_blown': damage.engine_blown if damage else 0,
            'engine_seized': damage.engine_seized if damage else 0,

            # === PENALTIES ===
            'penalties': lap.penalties if lap else 0,
            'warnings': lap.total_warnings if lap else 0,
            'corner_cutting_warnings': lap.corner_cutting_warnings if lap else 0,

            # === PIT ===
            'pit_status': PIT_STATUS_MAP.get(lap.pit_status, 'None') if lap else 'None',
            'pit_status_raw': lap.pit_status if lap else 0,
            'num_pit_stops': lap.num_pit_stops if lap else 0,

            # === G-FORCES ===
            'g_force_lat': round(motion.g_force_lateral, 2) if motion else 0,
            'g_force_lon': round(motion.g_force_longitudinal, 2) if motion else 0,

            # === TELEMETRY TRACES ===
            'throttle_trace': list(throttle_trace),
            'brake_trace': list(brake_trace),
            'speed_trace': list(speed_trace),

            # === ON TRACK COUNT ===
            'on_track_count': _count_on_track(),

            # === STATS ===
            'pps': telemetry_data.packets_per_second,
        }
        return data

    except Exception as e:
        print(f"Error get_player_telemetry: {e}")
        import traceback
        traceback.print_exc()
        return None


def _count_on_track():
    """Conta le auto attive in pista"""
    count = 0
    total = 0
    try:
        for i in range(22):
            if telemetry_data.participants[i].name != 'Unknown' and telemetry_data.lap_data[i].car_position > 0:
                total += 1
                if telemetry_data.lap_data[i].driver_status in (1, 2, 3, 4):  # Flying, In, Out, On Track
                    count += 1
    except Exception:
        pass
    return f"{count}/{total}"


def get_leaderboard_data():
    """Costruisce la leaderboard con dati broadcast-style"""
    try:
        with telemetry_data.lock:
            raw = telemetry_data.get_leaderboard()
            _update_car_fastest_laps()

        board = []
        for entry in raw:
            idx = entry['index']
            # ERS percentage per car
            ers_pct = 0
            try:
                ers_pct = round(telemetry_data.car_status[idx].ers_store_energy / 4000000 * 100)
            except Exception:
                pass

            # DRS status per car
            drs_active = 0
            drs_allowed = 0
            try:
                drs_active = telemetry_data.car_telemetry[idx].drs
                drs_allowed = telemetry_data.car_status[idx].drs_allowed
            except Exception:
                pass

            # Average tyre wear per car
            avg_wear = 0
            try:
                w = telemetry_data.car_damage[idx].tyres_wear
                avg_wear = round((w[0] + w[1] + w[2] + w[3]) / 4, 1)
            except Exception:
                pass

            # Fastest lap per car
            fastest_ms = car_fastest_laps.get(idx, 0)
            is_overall_fastest = (overall_fastest_lap['car_index'] == idx and fastest_ms > 0)

            # Team abbreviation (first letter or 3 chars)
            team_name = TEAM_IDS_MAP.get(entry['team_id'], '')
            team_abbr = team_name[:3].upper() if team_name else ''

            # Driver short name — show more chars for online lobbies
            name = entry['name']
            if ' ' in name:
                # Real F1 name: show last name (up to 3 chars)
                short_name = name.split()[-1][:3].upper()
            else:
                # Online gamertag: show full name (truncated to 12)
                short_name = name[:12]

            # Interval formatting
            if entry['position'] == 1:
                interval_text = format_time_ms(entry['last_lap_time_ms']) if entry['last_lap_time_ms'] > 0 else '--'
            else:
                interval_text = format_delta(entry['delta_to_car_in_front_ms'])

            # Best sectors per car
            car_s = car_best_sectors.get(idx, {'s1': 0, 's2': 0, 's3': 0})

            board.append({
                'position': entry['position'],
                'name': entry['name'],
                'short_name': short_name,
                'team': TEAM_IDS_MAP.get(entry['team_id'], ''),
                'team_abbr': team_abbr,
                'team_color': TEAM_COLORS.get(entry['team_id'], '#ffffff'),
                'race_number': entry['race_number'],
                'current_lap': entry['current_lap'],
                'last_lap': format_time_ms(entry['last_lap_time_ms']),
                'last_lap_raw': entry['last_lap_time_ms'],
                'fastest_lap': format_time_ms(fastest_ms) if fastest_ms > 0 else '--',
                'fastest_lap_raw': fastest_ms,
                'is_overall_fastest': is_overall_fastest,
                'delta_leader': format_delta(entry['delta_to_leader_ms']),
                'interval': interval_text,
                'delta_ahead': format_delta(entry['delta_to_car_in_front_ms']),
                'pit_status': PIT_STATUS_MAP.get(entry['pit_status'], ''),
                'pit_status_raw': entry['pit_status'],
                'num_pits': entry['num_pit_stops'],
                'penalties': entry['penalties'],
                'tyre': VISUAL_TYRE_MAP.get(entry['tyre_compound'], '-'),
                'tyre_compound_raw': entry['tyre_compound'],
                'tyre_age': entry['tyre_age'],
                'ers_pct': ers_pct,
                'drs_active': drs_active,
                'drs_allowed': drs_allowed,
                'avg_wear': avg_wear,
                'is_player': entry['is_player'],
                'driver_status': entry['driver_status'],
                'result_status': entry['result_status'],
                'best_s1': car_s['s1'],
                'best_s2': car_s['s2'],
                'best_s3': car_s['s3'],
            })
        return board
    except Exception:
        return []


def get_weather_forecast():
    """Previsioni meteo broadcast-style"""
    try:
        with telemetry_data.lock:
            forecasts = telemetry_data.session.weather_forecast[:8]
            accuracy = telemetry_data.session.forecast_accuracy

        result = []
        for f in forecasts:
            if f.time_offset == 0 and f.weather == 0 and f.track_temperature == 0:
                continue
            result.append({
                'time_offset': f.time_offset,
                'weather': WEATHER_MAP.get(f.weather, '?'),
                'weather_emoji': WEATHER_EMOJI.get(f.weather, '☁️'),
                'track_temp': f.track_temperature,
                'air_temp': f.air_temperature,
                'rain_pct': f.rain_percentage,
            })
        return {'forecasts': result, 'accuracy': 'Perfect' if accuracy == 0 else 'Approximate'}
    except Exception:
        return {'forecasts': [], 'accuracy': 'Unknown'}


_track_debug_logged = False

def get_car_positions():
    """Posizioni di tutte le auto sulla mappa del circuito"""
    global _track_debug_logged
    try:
        track_id = telemetry_data.session.track_id
        track = load_track(track_id)
        if not track:
            return None

        positions = []
        for i in range(22):
            lap = telemetry_data.lap_data[i]
            if lap.car_position <= 0 or telemetry_data.participants[i].name == 'Unknown':
                continue

            nx, nz = dist_to_position(lap.lap_distance, track)

            if not _track_debug_logged and i == telemetry_data.player_car_index:
                track_name = TRACK_IDS_MAP.get(track_id, 'Unknown')
                print(f"🗺️ Track: id={track_id}, name={track_name}")
                _track_debug_logged = True

            participant = telemetry_data.participants[i]
            team_color = TEAM_COLORS.get(participant.team_id, '#ffffff')
            name = participant.name
            short_name = name.split()[-1][:3].upper() if ' ' in name else name[:3].upper()

            positions.append({
                'x': round(nx, 5),
                'z': round(nz, 5),
                'pos': lap.car_position,
                'name': short_name,
                'color': team_color,
                'is_player': i == telemetry_data.player_car_index,
                'pit': lap.pit_status,
            })

        return {
            'track_id': track_id,
            'cars': positions,
        }
    except Exception as e:
        print(f"Error get_car_positions: {e}")
        return None


# ========================== STREAM ==========================

update_counter = 0

def telemetry_stream():
    """Thread that sends updates via WebSocket"""
    global update_counter
    print(" Telemetry stream started")
    while True:
        try:
            update_counter += 1
            with telemetry_data.lock:
                _update_best_sectors(telemetry_data.player_car_index)
                _update_trace(telemetry_data.player_car_index)
                data = get_player_telemetry()

            if data:
                payload = {'player': data}

                # Leaderboard: every 3 cycles (~100ms)
                if update_counter % 3 == 0:
                    _update_all_car_sectors()
                    leaderboard = get_leaderboard_data()
                    payload['leaderboard'] = leaderboard
                    payload['overall_best_sectors'] = dict(overall_best_sectors)

                # Weather: every 30 cycles (~1s)
                if update_counter % 30 == 0:
                    weather = get_weather_forecast()
                    payload['weather'] = weather

                # Car positions: every 2 cycles (~66ms)
                if update_counter % 2 == 0:
                    car_positions = get_car_positions()
                    if car_positions:
                        payload['car_positions'] = car_positions

                socketio.emit('telemetry_update', payload)

            time.sleep(0.035)  # ~28.57 Hz

        except Exception as e:
            print(f"Stream error: {e}")
            time.sleep(1)


# ========================== ROUTES ==========================

@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/track/<int:track_id>')
def api_track(track_id):
    data = get_track_json(track_id)
    if data:
        return jsonify(data)
    return jsonify({'error': 'Track not found'}), 404


@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')



# ========================== GUI & STARTUP ==========================

def start_udp_listener():
    global udp_thread
    if udp_thread is None or not udp_thread.is_alive():
        udp_thread = threading.Thread(target=listener, daemon=True)
        udp_thread.start()
        print("UDP Listener started")

def run_flask_server():
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)

def open_dashboard():
    webbrowser.open("http://localhost:5000")

def get_local_ip():
    """Find the local IP address of the machine for LAN access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def create_gui():
    import os
    import sys
    import ctypes

    try:
        myappid = 'z1.telemetry.server.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    root = tk.Tk()
    root.title("Z1 - F1 25 Telemetry Hub")
    root.geometry("450x450")
    root.configure(bg="#03060d")
    root.resizable(False, False)

    try:
        if getattr(sys, 'frozen', False) or '__compiled__' in globals():
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(base_path, "app_icon.ico")
        
        root.iconbitmap(default=icon_path)
    except Exception as e:
        print(f"Icona non caricata: {e}")

    title_font = font.Font(family="Helvetica", size=16, weight="bold")
    text_font = font.Font(family="Helvetica", size=10)

    lbl_title = tk.Label(root, text="Z1 TELEMETRY SERVER", font=title_font, fg="#00c8e8", bg="#03060d")
    lbl_title.pack(pady=(25, 10))

    instructions = (
        "1. Launch F1 25 and open the Telemetry settings.\n"
        "2. Ensure UDP data export is enabled on Port 20777.\n"
        "3. Click the button below to open the Dashboard."
    )
    lbl_inst = tk.Label(root, text=instructions, font=text_font, fg="#d8dce6", bg="#03060d", justify="left")
    lbl_inst.pack(pady=5)

    lbl_status = tk.Label(root, text="🟢 Server Active and listening...", 
                          font=font.Font(family="Helvetica", size=9, weight="bold"), 
                          fg="#00e676", bg="#03060d")
    lbl_status.pack(pady=10)

    btn_open = tk.Button(root, text="OPEN WEB DASHBOARD", font=font.Font(family="Helvetica", size=11, weight="bold"), 
                         bg="#00c8e8", fg="#000000", activebackground="#4cff50", cursor="hand2", 
                         relief="flat", padx=15, pady=8, command=open_dashboard)
    btn_open.pack(pady=10)

    local_ip = get_local_ip()
    dashboard_url = f"http://{local_ip}:5000"

    lbl_qr_inst = tk.Label(root, text=f"Scan to open on phone (same Wi-Fi):\n{dashboard_url}", 
                           font=text_font, fg="#d8dce6", bg="#03060d")
    lbl_qr_inst.pack(pady=(15, 5))

    try:
      
        qr = qrcode.QRCode(version=1, box_size=5, border=1)
        qr.add_data(dashboard_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        photo = ImageTk.PhotoImage(img)
        
        lbl_qr = tk.Label(root, image=photo, bg="#03060d", borderwidth=0)
        lbl_qr.image = photo 
        lbl_qr.pack(pady=5)
    except Exception as e:
        print(f"Errore QR: {e}")
        err_lbl = tk.Label(root, text="(Impossibile generare il QR Code)", fg="red", bg="#03060d")
        err_lbl.pack()

    def on_closing():
        root.destroy()
        import sys
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == '__main__':
    print("=" * 60)
    print("🏎️  F1 25 Broadcast Engineer Display - GUI Mode")
    print("=" * 60)

    preload_all_tracks()

    start_udp_listener()

    stream_thread = threading.Thread(target=telemetry_stream, daemon=True)
    stream_thread.start()

    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()

    create_gui()