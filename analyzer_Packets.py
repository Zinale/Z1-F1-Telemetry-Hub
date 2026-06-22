"""
F1 25 Telemetry - UDP Packet Parser & Data Storage
Riceve e decodifica tutti i pacchetti UDP inviati dal gioco F1 25
"""

import socket
import struct
import time
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# --- CONFIG ---
UDP_IP = "0.0.0.0"
UDP_PORT = 20777
BUFFER_SIZE = 4096
MAX_CARS = 22


# ========================== DATA STRUCTURES ==========================

@dataclass
class PacketHeader:
    packet_format: int = 0
    game_year: int = 0
    game_major_version: int = 0
    game_minor_version: int = 0
    packet_version: int = 0
    packet_id: int = 0
    session_uid: int = 0
    session_time: float = 0.0
    frame_identifier: int = 0
    overall_frame_identifier: int = 0
    player_car_index: int = 0
    secondary_player_car_index: int = 255


@dataclass
class CarMotionData:
    world_position_x: float = 0.0
    world_position_y: float = 0.0
    world_position_z: float = 0.0
    world_velocity_x: float = 0.0
    world_velocity_y: float = 0.0
    world_velocity_z: float = 0.0
    world_forward_dir_x: int = 0
    world_forward_dir_y: int = 0
    world_forward_dir_z: int = 0
    world_right_dir_x: int = 0
    world_right_dir_y: int = 0
    world_right_dir_z: int = 0
    g_force_lateral: float = 0.0
    g_force_longitudinal: float = 0.0
    g_force_vertical: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0


@dataclass
class WeatherForecastSample:
    session_type: int = 0
    time_offset: int = 0
    weather: int = 0
    track_temperature: int = 0
    track_temperature_change: int = 0
    air_temperature: int = 0
    air_temperature_change: int = 0
    rain_percentage: int = 0


@dataclass
class MarshalZone:
    zone_start: float = 0.0
    zone_flag: int = 0


@dataclass
class SessionData:
    weather: int = 0
    track_temperature: int = 0
    air_temperature: int = 0
    total_laps: int = 0
    track_length: int = 0
    session_type: int = 0
    track_id: int = -1
    formula: int = 0
    session_time_left: int = 0
    session_duration: int = 0
    pit_speed_limit: int = 0
    game_paused: int = 0
    is_spectating: int = 0
    spectator_car_index: int = 0
    sli_pro_native_support: int = 0
    num_marshal_zones: int = 0
    marshal_zones: List[MarshalZone] = field(default_factory=list)
    safety_car_status: int = 0
    network_game: int = 0
    num_weather_samples: int = 0
    weather_forecast: List[WeatherForecastSample] = field(default_factory=list)
    forecast_accuracy: int = 0
    ai_difficulty: int = 0
    pit_stop_window_ideal_lap: int = 0
    pit_stop_window_latest_lap: int = 0
    pit_stop_rejoin_position: int = 0
    num_safety_car_times: int = 0
    num_vsc_times: int = 0
    num_red_flags: int = 0


@dataclass
class LapData:
    last_lap_time_ms: int = 0
    current_lap_time_ms: int = 0
    sector1_time_ms: int = 0
    sector1_time_minutes: int = 0
    sector2_time_ms: int = 0
    sector2_time_minutes: int = 0
    delta_to_car_in_front_ms: int = 0
    delta_to_car_in_front_minutes: int = 0
    delta_to_leader_ms: int = 0
    delta_to_leader_minutes: int = 0
    lap_distance: float = 0.0
    total_distance: float = 0.0
    safety_car_delta: float = 0.0
    car_position: int = 0
    current_lap_num: int = 0
    pit_status: int = 0
    num_pit_stops: int = 0
    sector: int = 0
    current_lap_invalid: int = 0
    penalties: int = 0
    total_warnings: int = 0
    corner_cutting_warnings: int = 0
    num_unserved_dt_pens: int = 0
    num_unserved_sg_pens: int = 0
    grid_position: int = 0
    driver_status: int = 0
    result_status: int = 0
    pit_lane_timer_active: int = 0
    pit_lane_time_ms: int = 0
    pit_stop_timer_ms: int = 0
    pit_stop_should_serve_pen: int = 0
    speed_trap_fastest_speed: float = 0.0
    speed_trap_fastest_lap: int = 0


@dataclass
class ParticipantData:
    ai_controlled: int = 0
    driver_id: int = 255
    network_id: int = 0
    team_id: int = 255
    my_team: int = 0
    race_number: int = 0
    nationality: int = 0
    name: str = "Unknown"
    your_telemetry: int = 0
    show_online_names: int = 0
    tech_level: int = 0
    platform: int = 255


@dataclass
class CarTelemetryData:
    speed: int = 0
    throttle: float = 0.0
    steer: float = 0.0
    brake: float = 0.0
    clutch: int = 0
    gear: int = 0
    engine_rpm: int = 0
    drs: int = 0
    rev_lights_percent: int = 0
    rev_lights_bit_value: int = 0
    brakes_temperature: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    tyres_surface_temperature: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    tyres_inner_temperature: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    engine_temperature: int = 0
    tyres_pressure: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    surface_type: List[int] = field(default_factory=lambda: [0, 0, 0, 0])


@dataclass
class CarStatusData:
    traction_control: int = 0
    anti_lock_brakes: int = 0
    fuel_mix: int = 0
    front_brake_bias: int = 0
    pit_limiter_status: int = 0
    fuel_in_tank: float = 0.0
    fuel_capacity: float = 0.0
    fuel_remaining_laps: float = 0.0
    max_rpm: int = 0
    idle_rpm: int = 0
    max_gears: int = 0
    drs_allowed: int = 0
    drs_activation_distance: int = 0
    actual_tyre_compound: int = 0
    visual_tyre_compound: int = 0
    tyres_age_laps: int = 0
    vehicle_fia_flags: int = -1
    engine_power_ice: float = 0.0
    engine_power_mguk: float = 0.0
    ers_store_energy: float = 0.0
    ers_deploy_mode: int = 0
    ers_harvested_mguk: float = 0.0
    ers_harvested_mguh: float = 0.0
    ers_deployed_this_lap: float = 0.0
    network_paused: int = 0


@dataclass
class CarDamageData:
    tyres_wear: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    tyres_damage: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    brakes_damage: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    tyre_blisters: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    front_left_wing_damage: int = 0
    front_right_wing_damage: int = 0
    rear_wing_damage: int = 0
    floor_damage: int = 0
    diffuser_damage: int = 0
    sidepod_damage: int = 0
    drs_fault: int = 0
    ers_fault: int = 0
    gearbox_damage: int = 0
    engine_damage: int = 0
    engine_mguh_wear: int = 0
    engine_es_wear: int = 0
    engine_ce_wear: int = 0
    engine_ice_wear: int = 0
    engine_mguk_wear: int = 0
    engine_tc_wear: int = 0
    engine_blown: int = 0
    engine_seized: int = 0


@dataclass
class CarSetupData:
    front_wing: int = 0
    rear_wing: int = 0
    on_throttle: int = 0
    off_throttle: int = 0
    front_camber: float = 0.0
    rear_camber: float = 0.0
    front_toe: float = 0.0
    rear_toe: float = 0.0
    front_suspension: int = 0
    rear_suspension: int = 0
    front_anti_roll_bar: int = 0
    rear_anti_roll_bar: int = 0
    front_suspension_height: int = 0
    rear_suspension_height: int = 0
    brake_pressure: int = 0
    brake_bias: int = 0
    engine_braking: int = 0
    rear_left_tyre_pressure: float = 0.0
    rear_right_tyre_pressure: float = 0.0
    front_left_tyre_pressure: float = 0.0
    front_right_tyre_pressure: float = 0.0
    ballast: int = 0
    fuel_load: float = 0.0


@dataclass
class MotionExData:
    suspension_position: List[float] = field(default_factory=lambda: [0.0]*4)
    suspension_velocity: List[float] = field(default_factory=lambda: [0.0]*4)
    suspension_acceleration: List[float] = field(default_factory=lambda: [0.0]*4)
    wheel_speed: List[float] = field(default_factory=lambda: [0.0]*4)
    wheel_slip_ratio: List[float] = field(default_factory=lambda: [0.0]*4)
    wheel_slip_angle: List[float] = field(default_factory=lambda: [0.0]*4)
    wheel_lat_force: List[float] = field(default_factory=lambda: [0.0]*4)
    wheel_long_force: List[float] = field(default_factory=lambda: [0.0]*4)
    height_of_cog_above_ground: float = 0.0
    local_velocity_x: float = 0.0
    local_velocity_y: float = 0.0
    local_velocity_z: float = 0.0
    angular_velocity_x: float = 0.0
    angular_velocity_y: float = 0.0
    angular_velocity_z: float = 0.0
    angular_acceleration_x: float = 0.0
    angular_acceleration_y: float = 0.0
    angular_acceleration_z: float = 0.0
    front_wheels_angle: float = 0.0
    wheel_vert_force: List[float] = field(default_factory=lambda: [0.0]*4)
    front_aero_height: float = 0.0
    rear_aero_height: float = 0.0
    front_roll_angle: float = 0.0
    rear_roll_angle: float = 0.0
    chassis_yaw: float = 0.0
    chassis_pitch: float = 0.0


@dataclass
class FinalClassification:
    position: int = 0
    num_laps: int = 0
    grid_position: int = 0
    points: int = 0
    num_pit_stops: int = 0
    result_status: int = 0
    result_reason: int = 0
    best_lap_time_ms: int = 0
    total_race_time: float = 0.0
    penalties_time: int = 0
    num_penalties: int = 0
    num_tyre_stints: int = 0
    tyre_stints_actual: List[int] = field(default_factory=lambda: [0]*8)
    tyre_stints_visual: List[int] = field(default_factory=lambda: [0]*8)
    tyre_stints_end_laps: List[int] = field(default_factory=lambda: [0]*8)


# ========================== EVENT DATA STRUCTURES ==========================

@dataclass
class FastestLap:
    vehicle_idx: int = 0
    lap_time: float = 0.0

@dataclass
class Retirement:
    vehicle_idx: int = 0
    reason: int = 0

@dataclass
class DRSDisabled:
    reason: int = 0

@dataclass
class TeamMateInPits:
    vehicle_idx: int = 0

@dataclass
class RaceWinner:
    vehicle_idx: int = 0

@dataclass
class Penalty:
    penalty_type: int = 0
    infringement_type: int = 0
    vehicle_idx: int = 0
    other_vehicle_idx: int = 0
    time: int = 0
    lap_num: int = 0
    places_gained: int = 0

@dataclass
class SpeedTrap:
    vehicle_idx: int = 0
    speed: float = 0.0
    is_overall_fastest_in_session: int = 0
    is_driver_fastest_in_session: int = 0
    fastest_vehicle_idx_in_session: int = 0
    fastest_speed_in_session: float = 0.0

@dataclass
class StartLights:
    num_lights: int = 0

@dataclass
class DriveThroughPenaltyServed:
    vehicle_idx: int = 0

@dataclass
class StopGoPenaltyServed:
    vehicle_idx: int = 0

@dataclass
class Overtake:
    overtaking_vehicle_idx: int = 0
    being_overtaken_vehicle_idx: int = 0

@dataclass
class SafetyCar:
    safety_car_type: int = 0
    event_type: int = 0

@dataclass
class Collision:
    vehicle_idx1: int = 0
    vehicle_idx2: int = 0

@dataclass
class EventData:
    event_string_code: str = ""
    event_details: Optional[object] = None


# ========================== MAIN STORAGE ==========================

class TelemetryData:
    """Main class for storing all telemetry data"""
    def __init__(self):
        self.lock = threading.Lock()

        # Global info
        self.session_uid: int = 0
        self.player_car_index: int = 0
        self.game_year: int = 0
        self.game_version: str = "0.0"

        # Statistics
        self.packets_per_second: int = 0
        self.last_packet_id: int = -1
        self.last_frame_identifier: int = 0
        self.session_time: float = 0.0

        # Session data
        self.session = SessionData()

        # Data for each car (22 cars)
        self.motion_data = [CarMotionData() for _ in range(MAX_CARS)]
        self.lap_data = [LapData() for _ in range(MAX_CARS)]
        self.participants = [ParticipantData() for _ in range(MAX_CARS)]
        self.car_telemetry = [CarTelemetryData() for _ in range(MAX_CARS)]
        self.car_status = [CarStatusData() for _ in range(MAX_CARS)]
        self.car_damage = [CarDamageData() for _ in range(MAX_CARS)]
        self.car_setups = [CarSetupData() for _ in range(MAX_CARS)]
        self.final_classifications = [FinalClassification() for _ in range(MAX_CARS)]

        # Extended data (player only)
        self.motion_ex = MotionExData()

        # Events
        self.events: List[EventData] = []
        self.last_event: Optional[EventData] = None

    def get_player_data(self) -> Dict:
        idx = self.player_car_index
        if idx < 0 or idx >= MAX_CARS:
            return {}
        return {
            'motion': self.motion_data[idx],
            'lap': self.lap_data[idx],
            'participant': self.participants[idx],
            'telemetry': self.car_telemetry[idx],
            'status': self.car_status[idx],
            'damage': self.car_damage[idx],
            'setup': self.car_setups[idx],
            'motion_ex': self.motion_ex
        }

    def get_leaderboard(self) -> List[Dict]:
        leaderboard = []
        for i in range(MAX_CARS):
            if self.lap_data[i].car_position > 0 and self.participants[i].name != "Unknown":
                leaderboard.append({
                    'index': i,
                    'position': self.lap_data[i].car_position,
                    'name': self.participants[i].name,
                    'team_id': self.participants[i].team_id,
                    'race_number': self.participants[i].race_number,
                    'current_lap': self.lap_data[i].current_lap_num,
                    'last_lap_time_ms': self.lap_data[i].last_lap_time_ms,
                    'delta_to_leader_ms': self.lap_data[i].delta_to_leader_ms,
                    'delta_to_car_in_front_ms': self.lap_data[i].delta_to_car_in_front_ms,
                    'pit_status': self.lap_data[i].pit_status,
                    'num_pit_stops': self.lap_data[i].num_pit_stops,
                    'penalties': self.lap_data[i].penalties,
                    'tyre_compound': self.car_status[i].visual_tyre_compound,
                    'tyre_age': self.car_status[i].tyres_age_laps,
                    'driver_status': self.lap_data[i].driver_status,
                    'result_status': self.lap_data[i].result_status,
                    'is_player': i == self.player_car_index,
                })
        leaderboard.sort(key=lambda x: x['position'])
        return leaderboard

    def update_from_header(self, header: PacketHeader):
        self.session_uid = header.session_uid
        self.player_car_index = header.player_car_index
        self.last_packet_id = header.packet_id
        self.last_frame_identifier = header.frame_identifier
        self.session_time = header.session_time
        if self.game_year == 0:
            self.game_year = header.game_year
            self.game_version = f"{header.game_major_version}.{header.game_minor_version:02d}"


# ========================== GLOBAL INSTANCE ==========================

telemetry_data = TelemetryData()
data_lock = threading.Lock()


# ========================== PARSING ==========================

def parse_header(data: bytes) -> Optional[PacketHeader]:
    if len(data) < 29:
        return None
    h = struct.unpack('<HBBBBBQfIIBB', data[:29])
    return PacketHeader(
        packet_format=h[0], game_year=h[1],
        game_major_version=h[2], game_minor_version=h[3],
        packet_version=h[4], packet_id=h[5],
        session_uid=h[6], session_time=h[7],
        frame_identifier=h[8], overall_frame_identifier=h[9],
        player_car_index=h[10], secondary_player_car_index=h[11]
    )


def _parse_motion(data: bytes):
    """Packet ID 0 - Motion Data (60 bytes per car)"""
    car_motion_size = 60
    for i in range(MAX_CARS):
        offset = 29 + (i * car_motion_size)
        if len(data) < offset + car_motion_size:
            break
        try:
            vals = struct.unpack('<ffffffhhhhhhffffff', data[offset:offset+60])
            with telemetry_data.lock:
                m = telemetry_data.motion_data[i]
                m.world_position_x = vals[0]
                m.world_position_y = vals[1]
                m.world_position_z = vals[2]
                m.world_velocity_x = vals[3]
                m.world_velocity_y = vals[4]
                m.world_velocity_z = vals[5]
                m.world_forward_dir_x = vals[6]
                m.world_forward_dir_y = vals[7]
                m.world_forward_dir_z = vals[8]
                m.world_right_dir_x = vals[9]
                m.world_right_dir_y = vals[10]
                m.world_right_dir_z = vals[11]
                m.g_force_lateral = vals[12]
                m.g_force_longitudinal = vals[13]
                m.g_force_vertical = vals[14]
                m.yaw = vals[15]
                m.pitch = vals[16]
                m.roll = vals[17]
        except Exception:
            pass


def _parse_session(data: bytes):
    """Packet ID 1 - Session Data"""
    try:
        if len(data) < 47:
            return
        basic = struct.unpack('<BbbBHBbBHHBBBBB', data[29:47])
        with telemetry_data.lock:
            s = telemetry_data.session
            s.weather = basic[0]
            s.track_temperature = basic[1]
            s.air_temperature = basic[2]
            s.total_laps = basic[3]
            s.track_length = basic[4]
            s.session_type = basic[5]
            s.track_id = basic[6]
            s.formula = basic[7]
            s.session_time_left = basic[8]
            s.session_duration = basic[9]
            s.pit_speed_limit = basic[10]
            s.game_paused = basic[11]
            s.is_spectating = basic[12]
            s.spectator_car_index = basic[13]
            s.sli_pro_native_support = basic[14]

            s.num_marshal_zones = struct.unpack('<B', data[47:48])[0]
            mz = struct.unpack('<' + 'fb' * 21, data[48:48 + 21 * 5])
            s.marshal_zones = [MarshalZone(zone_start=mz[j*2], zone_flag=mz[j*2+1])
                               for j in range(s.num_marshal_zones)]
            offset = 48 + 21 * 5  # 153
            s.safety_car_status = struct.unpack('<B', data[offset:offset+1])[0]; offset += 1
            s.network_game = struct.unpack('<B', data[offset:offset+1])[0]; offset += 1
            s.num_weather_samples = struct.unpack('<B', data[offset:offset+1])[0]; offset += 1

            wf = struct.unpack('<' + 'BBBbbbbB' * 64, data[offset:offset + 64 * 8])
            s.weather_forecast = [WeatherForecastSample(
                session_type=wf[j*8], time_offset=wf[j*8+1],
                weather=wf[j*8+2], track_temperature=wf[j*8+3],
                track_temperature_change=wf[j*8+4], air_temperature=wf[j*8+5],
                air_temperature_change=wf[j*8+6], rain_percentage=wf[j*8+7]
            ) for j in range(64)]
            offset += 64 * 8

            s.forecast_accuracy = struct.unpack('<B', data[offset:offset+1])[0]; offset += 1
            s.ai_difficulty = struct.unpack('<B', data[offset:offset+1])[0]; offset += 1
            offset += 12  # Skip link identifiers

            pit = struct.unpack('<BBB', data[offset:offset+3])
            s.pit_stop_window_ideal_lap = pit[0]
            s.pit_stop_window_latest_lap = pit[1]
            s.pit_stop_rejoin_position = pit[2]
            offset += 3
            offset += 20  # Skip assists, gameMode, ruleSet, etc.

            sc = struct.unpack('<BBB', data[offset:offset+3])
            s.num_safety_car_times = sc[0]
            s.num_vsc_times = sc[1]
            s.num_red_flags = sc[2]
    except Exception as e:
        print(f"Error parsing session: {e}")


def _parse_lap_data(data: bytes):
    """Packet ID 2 - Lap Data (57 bytes per car)"""
    lap_data_size = 57
    for i in range(MAX_CARS):
        offset = 29 + (i * lap_data_size)
        if len(data) < offset + lap_data_size:
            break
        try:
            chunk = data[offset:offset + lap_data_size]
            vals = struct.unpack('<IIHBHBHBHBfff' + 'B'*15 + 'HHBfB', chunk[:57])
            with telemetry_data.lock:
                lap = telemetry_data.lap_data[i]
                lap.last_lap_time_ms = vals[0]
                lap.current_lap_time_ms = vals[1]
                lap.sector1_time_ms = vals[2]
                lap.sector1_time_minutes = vals[3]
                lap.sector2_time_ms = vals[4]
                lap.sector2_time_minutes = vals[5]
                lap.delta_to_car_in_front_ms = vals[6]
                lap.delta_to_car_in_front_minutes = vals[7]
                lap.delta_to_leader_ms = vals[8]
                lap.delta_to_leader_minutes = vals[9]
                lap.lap_distance = vals[10]
                lap.total_distance = vals[11]
                lap.safety_car_delta = vals[12]
                lap.car_position = vals[13]
                lap.current_lap_num = vals[14]
                lap.pit_status = vals[15]
                lap.num_pit_stops = vals[16]
                lap.sector = vals[17]
                lap.current_lap_invalid = vals[18]
                lap.penalties = vals[19]
                lap.total_warnings = vals[20]
                lap.corner_cutting_warnings = vals[21]
                lap.num_unserved_dt_pens = vals[22]
                lap.num_unserved_sg_pens = vals[23]
                lap.grid_position = vals[24]
                lap.driver_status = vals[25]
                lap.result_status = vals[26]
                lap.pit_lane_timer_active = vals[27]
                lap.pit_lane_time_ms = vals[28]
                lap.pit_stop_timer_ms = vals[29]
                lap.speed_trap_fastest_speed = vals[30]
                lap.speed_trap_fastest_lap = vals[31]
        except Exception:
            pass


def _parse_event(data: bytes):
    """Packet ID 3 - Event Data"""
    try:
        offset = 29
        event_code = data[offset:offset+4].decode('utf-8', errors='ignore').rstrip('\x00')
        offset += 4
        event_details = None

        if event_code == "FTLP":
            d = struct.unpack('<Bf', data[offset:offset+5])
            event_details = FastestLap(vehicle_idx=d[0], lap_time=d[1])
        elif event_code == "RTMT":
            event_details = Retirement(
                vehicle_idx=struct.unpack('<B', data[offset:offset+1])[0],
                reason=struct.unpack('<B', data[offset+1:offset+2])[0])
        elif event_code == "DRSD":
            event_details = DRSDisabled(reason=struct.unpack('<B', data[offset:offset+1])[0])
        elif event_code == "TMPT":
            event_details = TeamMateInPits(vehicle_idx=struct.unpack('<B', data[offset:offset+1])[0])
        elif event_code == "RCWN":
            event_details = RaceWinner(vehicle_idx=struct.unpack('<B', data[offset:offset+1])[0])
        elif event_code == "PENA":
            d = struct.unpack('<BBBBBBB', data[offset:offset+7])
            event_details = Penalty(
                penalty_type=d[0], infringement_type=d[1],
                vehicle_idx=d[2], other_vehicle_idx=d[3],
                time=d[4], lap_num=d[5], places_gained=d[6])
        elif event_code == "SPTP":
            d = struct.unpack('<BfBBBf', data[offset:offset+14])
            event_details = SpeedTrap(
                vehicle_idx=d[0], speed=d[1],
                is_overall_fastest_in_session=d[2],
                is_driver_fastest_in_session=d[3],
                fastest_vehicle_idx_in_session=d[4],
                fastest_speed_in_session=d[5])
        elif event_code == "STLG":
            event_details = StartLights(num_lights=struct.unpack('<B', data[offset:offset+1])[0])
        elif event_code == "DTSV":
            event_details = DriveThroughPenaltyServed(vehicle_idx=struct.unpack('<B', data[offset:offset+1])[0])
        elif event_code == "SGSV":
            event_details = StopGoPenaltyServed(vehicle_idx=struct.unpack('<B', data[offset:offset+1])[0])
        elif event_code == "OVTK":
            d = struct.unpack('<BB', data[offset:offset+2])
            event_details = Overtake(overtaking_vehicle_idx=d[0], being_overtaken_vehicle_idx=d[1])
        elif event_code == "SCAR":
            d = struct.unpack('<BB', data[offset:offset+2])
            event_details = SafetyCar(safety_car_type=d[0], event_type=d[1])
        elif event_code == "COLL":
            d = struct.unpack('<BB', data[offset:offset+2])
            event_details = Collision(vehicle_idx1=d[0], vehicle_idx2=d[1])

        event = EventData(event_string_code=event_code, event_details=event_details)
        with telemetry_data.lock:
            telemetry_data.last_event = event
            telemetry_data.events.append(event)
            if len(telemetry_data.events) > 100:
                telemetry_data.events.pop(0)
    except Exception as e:
        print(f"Error parsing event: {e}")


def _parse_participants(data: bytes):
    """Packet ID 4 - Participants (57 bytes per participant in F1 25)"""
    try:
        if len(data) < 30:
            return
        header = parse_header(data)
        if not header:
            return
        num_active = struct.unpack('<B', data[29:30])[0]
        participant_size = 57
        player_idx = header.player_car_index

        for i in range(MAX_CARS):
            offset = 30 + (i * participant_size)
            if len(data) < offset + participant_size:
                break
            try:
                chunk = data[offset:offset + participant_size]
                basic = struct.unpack('<BBBBBBB', chunk[:7])
                name = chunk[7:39].decode('utf-8', errors='ignore').split('\x00')[0].strip()
                remaining = struct.unpack('<BBHB', chunk[39:44]) if len(chunk) >= 44 else (0, 0, 0, 0)

                with telemetry_data.lock:
                    p = telemetry_data.participants[i]
                    p.ai_controlled = basic[0]
                    p.driver_id = basic[1]
                    p.network_id = basic[2]
                    p.team_id = basic[3]
                    p.my_team = basic[4]
                    p.race_number = basic[5]
                    p.nationality = basic[6]
                    p.your_telemetry = remaining[0]
                    p.show_online_names = remaining[1]
                    p.tech_level = remaining[2]
                    p.platform = remaining[3]
                    if name:
                        p.name = name
                    elif i == player_idx:
                        p.name = "Player"
                    else:
                        p.name = f"Driver {i+1}"
            except Exception:
                pass
    except Exception as e:
        print(f"Error parsing participants: {e}")


def _parse_car_setup(data: bytes):
    """Packet ID 5 - Car Setup (50 bytes per car)"""
    setup_size = 50
    for i in range(MAX_CARS):
        offset = 29 + (i * setup_size)
        if len(data) < offset + setup_size:
            break
        try:
            chunk = data[offset:offset + setup_size]
            vals = struct.unpack('<BBBBffffBBBBBBBBBffffBf', chunk[:50])
            with telemetry_data.lock:
                s = telemetry_data.car_setups[i]
                s.front_wing = vals[0]; s.rear_wing = vals[1]
                s.on_throttle = vals[2]; s.off_throttle = vals[3]
                s.front_camber = vals[4]; s.rear_camber = vals[5]
                s.front_toe = vals[6]; s.rear_toe = vals[7]
                s.front_suspension = vals[8]; s.rear_suspension = vals[9]
                s.front_anti_roll_bar = vals[10]; s.rear_anti_roll_bar = vals[11]
                s.front_suspension_height = vals[12]; s.rear_suspension_height = vals[13]
                s.brake_pressure = vals[14]; s.brake_bias = vals[15]
                s.engine_braking = vals[16]
                s.rear_left_tyre_pressure = vals[17]; s.rear_right_tyre_pressure = vals[18]
                s.front_left_tyre_pressure = vals[19]; s.front_right_tyre_pressure = vals[20]
                s.ballast = vals[21]; s.fuel_load = vals[22]
        except Exception:
            pass


def _parse_car_telemetry(data: bytes):
    """Packet ID 6 - Car Telemetry (60 bytes per car)"""
    telemetry_size = 60
    for i in range(MAX_CARS):
        offset = 29 + (i * telemetry_size)
        if len(data) < offset + telemetry_size:
            break
        try:
            chunk = data[offset:offset + telemetry_size]
            basic = struct.unpack('<HfffBbH', chunk[:18])
            with telemetry_data.lock:
                t = telemetry_data.car_telemetry[i]
                t.speed = basic[0]; t.throttle = basic[1]
                t.steer = basic[2]; t.brake = basic[3]
                t.clutch = basic[4]; t.gear = basic[5]
                t.engine_rpm = basic[6]
                t.drs = chunk[18]; t.rev_lights_percent = chunk[19]
                t.rev_lights_bit_value = struct.unpack('<H', chunk[20:22])[0]
                t.brakes_temperature = list(struct.unpack('<HHHH', chunk[22:30]))
                t.tyres_surface_temperature = list(chunk[30:34])
                t.tyres_inner_temperature = list(chunk[34:38])
                t.engine_temperature = struct.unpack('<H', chunk[38:40])[0]
                t.tyres_pressure = list(struct.unpack('<ffff', chunk[40:56]))
                t.surface_type = list(chunk[56:60])
        except Exception:
            pass


def _parse_car_status(data: bytes):
    """Packet ID 7 - Car Status (55 bytes per car)"""
    status_size = 55
    for i in range(MAX_CARS):
        offset = 29 + (i * status_size)
        if len(data) < offset + status_size:
            break
        try:
            chunk = data[offset:offset + status_size]
            part1 = struct.unpack('<BBBBB', chunk[0:5])
            part2 = struct.unpack('<fff', chunk[5:17])
            part3 = struct.unpack('<HH', chunk[17:21])
            part4 = struct.unpack('<BBH', chunk[21:25])
            part5 = struct.unpack('<BBBb', chunk[25:29])
            part6 = struct.unpack('<fff', chunk[29:41])
            ers_deploy_mode = chunk[41]
            part7 = struct.unpack('<fff', chunk[42:54])

            with telemetry_data.lock:
                s = telemetry_data.car_status[i]
                s.traction_control = part1[0]; s.anti_lock_brakes = part1[1]
                s.fuel_mix = part1[2]; s.front_brake_bias = part1[3]
                s.pit_limiter_status = part1[4]
                s.fuel_in_tank = part2[0]; s.fuel_capacity = part2[1]
                s.fuel_remaining_laps = part2[2]
                s.max_rpm = part3[0]; s.idle_rpm = part3[1]
                s.max_gears = part4[0]; s.drs_allowed = part4[1]
                s.drs_activation_distance = part4[2]
                s.actual_tyre_compound = part5[0]; s.visual_tyre_compound = part5[1]
                s.tyres_age_laps = part5[2]; s.vehicle_fia_flags = part5[3]
                s.engine_power_ice = part6[0]; s.engine_power_mguk = part6[1]
                s.ers_store_energy = part6[2]
                s.ers_deploy_mode = ers_deploy_mode
                s.ers_harvested_mguk = part7[0]; s.ers_harvested_mguh = part7[1]
                s.ers_deployed_this_lap = part7[2]
        except Exception:
            pass


def _parse_final_classification(data: bytes):
    """Packet ID 8 - Final Classification (46 bytes per entry)"""
    try:
        if len(data) < 30:
            return
        num_active = struct.unpack('<B', data[29:30])[0]
        for i in range(min(num_active, MAX_CARS)):
            offset = 30 + (i * 46)
            if len(data) < offset + 46:
                break
            try:
                chunk = data[offset:offset + 46]
                vals = struct.unpack('<BBBBBBBIdBBB' + 'B'*8 + 'B'*8 + 'B'*8, chunk[:46])
                with telemetry_data.lock:
                    fc = telemetry_data.final_classifications[i]
                    fc.position = vals[0]; fc.num_laps = vals[1]
                    fc.grid_position = vals[2]; fc.points = vals[3]
                    fc.num_pit_stops = vals[4]; fc.result_status = vals[5]
                    fc.result_reason = vals[6]; fc.best_lap_time_ms = vals[7]
                    fc.total_race_time = vals[8]; fc.penalties_time = vals[9]
                    fc.num_penalties = vals[10]; fc.num_tyre_stints = vals[11]
                    fc.tyre_stints_actual = list(vals[12:20])
                    fc.tyre_stints_visual = list(vals[20:28])
                    fc.tyre_stints_end_laps = list(vals[28:36])
            except Exception:
                pass
    except Exception as e:
        print(f"Error parsing final classification: {e}")


def _parse_car_damage(data: bytes):
    """Packet ID 10 - Car Damage (46 bytes per car)"""
    damage_size = 46
    for i in range(MAX_CARS):
        offset = 29 + (i * damage_size)
        if len(data) < offset + damage_size:
            break
        try:
            chunk = data[offset:offset + damage_size]
            tyres_wear = struct.unpack('<ffff', chunk[0:16])
            tyres_damage = struct.unpack('<BBBB', chunk[16:20])
            brakes_damage = struct.unpack('<BBBB', chunk[20:24])
            tyre_blisters = struct.unpack('<BBBB', chunk[24:28])
            rest = struct.unpack('<BBBBBBBBBBBBBBBBBB', chunk[28:46])

            with telemetry_data.lock:
                d = telemetry_data.car_damage[i]
                d.tyres_wear = list(tyres_wear)
                d.tyres_damage = list(tyres_damage)
                d.brakes_damage = list(brakes_damage)
                d.tyre_blisters = list(tyre_blisters)
                d.front_left_wing_damage = rest[0]; d.front_right_wing_damage = rest[1]
                d.rear_wing_damage = rest[2]; d.floor_damage = rest[3]
                d.diffuser_damage = rest[4]; d.sidepod_damage = rest[5]
                d.drs_fault = rest[6]; d.ers_fault = rest[7]
                d.gearbox_damage = rest[8]; d.engine_damage = rest[9]
                d.engine_mguh_wear = rest[10]; d.engine_es_wear = rest[11]
                d.engine_ce_wear = rest[12]; d.engine_ice_wear = rest[13]
                d.engine_mguk_wear = rest[14]; d.engine_tc_wear = rest[15]
                d.engine_blown = rest[16]; d.engine_seized = rest[17]
        except Exception:
            pass


def _parse_motion_ex(data: bytes):
    """Packet ID 13 - Motion Ex Data (solo giocatore)"""
    try:
        offset = 29
        # 32 floats per le prime 8 liste di 4 float = 128 bytes
        # poi 1 float (height) + 9 floats (local/angular vel/accel) + 1 float (front_wheels_angle)
        # + 4 floats (wheel_vert_force) + 6 floats (aero/roll/chassis)
        # Totale: 32 + 1 + 9 + 1 + 4 + 6 = 53 floats = 212 bytes
        if len(data) < offset + 212:
            return

        vals = struct.unpack('<' + 'f' * 53, data[offset:offset + 212])
        with telemetry_data.lock:
            mx = telemetry_data.motion_ex
            mx.suspension_position = list(vals[0:4])
            mx.suspension_velocity = list(vals[4:8])
            mx.suspension_acceleration = list(vals[8:12])
            mx.wheel_speed = list(vals[12:16])
            mx.wheel_slip_ratio = list(vals[16:20])
            mx.wheel_slip_angle = list(vals[20:24])
            mx.wheel_lat_force = list(vals[24:28])
            mx.wheel_long_force = list(vals[28:32])
            mx.height_of_cog_above_ground = vals[32]
            mx.local_velocity_x = vals[33]; mx.local_velocity_y = vals[34]; mx.local_velocity_z = vals[35]
            mx.angular_velocity_x = vals[36]; mx.angular_velocity_y = vals[37]; mx.angular_velocity_z = vals[38]
            mx.angular_acceleration_x = vals[39]; mx.angular_acceleration_y = vals[40]; mx.angular_acceleration_z = vals[41]
            mx.front_wheels_angle = vals[42]
            mx.wheel_vert_force = list(vals[43:47])
            mx.front_aero_height = vals[47]; mx.rear_aero_height = vals[48]
            mx.front_roll_angle = vals[49]; mx.rear_roll_angle = vals[50]
            mx.chassis_yaw = vals[51]; mx.chassis_pitch = vals[52]
    except Exception as e:
        print(f"Error parsing motion ex: {e}")


# ========================== LISTENER ==========================

def listener():
    """Thread listener UDP che riceve e parsa i pacchetti F1 25"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((UDP_IP, UDP_PORT))
    except Exception as e:
        print(f"Cannot bind to {UDP_IP}:{UDP_PORT}: {e}")
        return

    print(f" UDP Listener bound on {UDP_IP}:{UDP_PORT}")
    pkt_count = 0
    t_start = time.time()

    while True:
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            header = parse_header(data)
            if not header:
                continue

            with telemetry_data.lock:
                telemetry_data.update_from_header(header)

            # PPS stats
            pkt_count += 1
            if time.time() - t_start > 1.0:
                with telemetry_data.lock:
                    telemetry_data.packets_per_second = pkt_count
                pkt_count = 0
                t_start = time.time()

            # Dispatch per tipo di pacchetto
            pid = header.packet_id
            if pid == 0:
                _parse_motion(data)
            elif pid == 1:
                _parse_session(data)
            elif pid == 2:
                _parse_lap_data(data)
            elif pid == 3:
                _parse_event(data)
            elif pid == 4:
                _parse_participants(data)
            elif pid == 5:
                _parse_car_setup(data)
            elif pid == 6:
                _parse_car_telemetry(data)
            elif pid == 7:
                _parse_car_status(data)
            elif pid == 8:
                _parse_final_classification(data)
            elif pid == 10:
                _parse_car_damage(data)
            elif pid == 13:
                _parse_motion_ex(data)

        except Exception as e:
            print(f"Packet error: {e}")
            import traceback
            traceback.print_exc()
