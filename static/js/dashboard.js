/**
 * F1 25 Broadcast Engineer Display — Real-time Socket.IO Client
 * Handles: player telemetry, track map, leaderboard with ERS/DRS,
 *          telemetry trace graphs, car silhouette with tyre data
 */

(function () {
    'use strict';

    /* ======================== SOCKET.IO ======================== */
    const socket = io({ reconnection: true, reconnectionDelay: 1000, reconnectionAttempts: Infinity });

    socket.on('connect', () => console.log('Connected'));
    socket.on('disconnect', () => console.log('Disconnected'));

    /* ======================== HELPERS ======================== */
    const $ = id => document.getElementById(id);
    const setText = (id, v) => { const el = $(id); if (el) el.textContent = v ?? '--'; };
    const clamp = (v, lo = 0, hi = 100) => Math.max(lo, Math.min(hi, v));

    function fmtSessionTime(s) {
        if (!s || s <= 0) return '--:--';
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const sec = Math.floor(s % 60);
        if (h > 0) return `${h}:${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;
        return `${m}:${sec.toString().padStart(2, '0')}`;
    }

    function fmtSectorMs(ms) {
        if (!ms || ms <= 0) return '--:--.---';
        const minutes = Math.floor(ms / 60000);
        const seconds = Math.floor((ms % 60000) / 1000);
        const millis = ms % 1000;
        if (minutes > 0)
            return `${minutes}:${seconds.toString().padStart(2,'0')}.${millis.toString().padStart(3,'0')}`;
        return `${seconds}.${millis.toString().padStart(3,'0')}`;
    }

    function getCurrentTimeStr() {
        const now = new Date();
        return `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}`;
    }

    function tyreColor(temp) {
        if (temp <= 60) return '#42a5f5';
        if (temp <= 90) return '#00e676';
        if (temp <= 110) return '#ffd600';
        return '#ff1744';
    }

    function wheelColor(wear) {
        if (wear >= 60) return '#ff1744';
        if (wear >= 35) return '#ffd600';
        return '#00e676';
    }

    /* ======================== TEAM ACCENT COLORS ======================== */
    const TEAM_COLORS = {
        'Mercedes':     '#00d2be',
        'Ferrari':      '#dc0000',
        'Red Bull':     '#3671C6',
        'Williams':     '#64C4FF',
        'Aston Martin': '#358C75',
        'Alpine':       '#0090FF',
        'RB':           '#6692FF',
        'Haas':         '#B6BABD',
        'McLaren':      '#FF8700',
        'Sauber':       '#52E252',
        'F1 Generic':   '#00c8e8',
        'F1 Custom Team': '#00c8e8',
        'Konnersport':  '#00c8e8',
        'APXGP \'24':  '#00c8e8',
        'APXGP \'25':  '#00c8e8',
    };
    const DEFAULT_ACCENT = '#00c8e8';

    // Current accent as {r, g, b} and hex
    let accentRGB = { r: 0, g: 200, b: 232 };
    let accentHex = DEFAULT_ACCENT;
    let currentTeamName = '';

    function hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result
            ? { r: parseInt(result[1], 16), g: parseInt(result[2], 16), b: parseInt(result[3], 16) }
            : { r: 0, g: 200, b: 232 };
    }

    function accentRGBA(alpha) {
        return `rgba(${accentRGB.r}, ${accentRGB.g}, ${accentRGB.b}, ${alpha})`;
    }

    function applyTeamAccent(teamName) {
        if (!teamName || teamName === currentTeamName) return;
        currentTeamName = teamName;
        accentHex = TEAM_COLORS[teamName] || DEFAULT_ACCENT;
        accentRGB = hexToRgb(accentHex);

        const root = document.documentElement.style;
        root.setProperty('--cyan', accentHex);
        root.setProperty('--cyan-dim', accentRGBA(0.15));
        root.setProperty('--cyan-glow', accentRGBA(0.35));
        root.setProperty('--border', accentRGBA(0.18));
        root.setProperty('--border-dim', accentRGBA(0.08));
        root.setProperty('--border-glow', accentRGBA(0.3));
    }

    /* ======================== RIGHT TAB SWITCHING ======================== */
    (function initRightTabs() {
        const tabs = document.querySelectorAll('.right-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                document.querySelectorAll('.right-tab-content').forEach(content => {
                    content.style.display = 'none';
                });
                const el = document.getElementById('rtab-' + target);
                if (el) el.style.display = 'flex';
            });
        });
        // Show leaderboard by default
        const leaderboardContent = document.getElementById('rtab-leaderboard');
        if (leaderboardContent) leaderboardContent.style.display = 'flex';
    })();

    /* ======================== GP FLAG ======================== */
    // Track name → ISO 3166-1 alpha-2 country code for flagcdn.com
    const trackCountryCodes = {
        'Melbourne':        'au',
        'Shanghai':         'cn',
        'Sakhir (Bahrain)': 'bh',
        'Catalunya':        'es',
        'Monaco':           'mc',
        'Montreal':         'ca',
        'Silverstone':      'gb',
        'Hungaroring':      'hu',
        'Spa':              'be',
        'Monza':            'it',
        'Singapore':        'sg',
        'Suzuka':           'jp',
        'Abu Dhabi':        'ae',
        'Texas':            'us',
        'Brazil':           'br',
        'Austria':          'at',
        'Mexico':           'mx',
        'Baku (Azerbaijan)':'az',
        'Zandvoort':        'nl',
        'Imola':            'it',
        'Jeddah':           'sa',
        'Miami':            'us',
        'Las Vegas':        'us',
        'Losail':           'qa',
    };
    let currentFlagTrack = '';

    function updateGPFlag(trackName) {
        if (trackName === currentFlagTrack) return;
        currentFlagTrack = trackName;
        const img = $('gp-flag-img');
        if (!img) return;
        const code = trackCountryCodes[trackName];
        if (code) {
            img.src = 'https://flagcdn.com/w80/' + code + '.png';
            img.alt = code.toUpperCase();
        } else {
            img.src = 'https://flagcdn.com/w80/un.png';
            img.alt = 'UN';
        }
    }

    /* ======================== STEERING WHEEL CANVAS ======================== */
    function drawSteeringWheel(steerPct) {
        const canvas = $('steer-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        const W = 120, H = 120;
        canvas.width = W;
        canvas.height = H;
        ctx.clearRect(0, 0, W, H);

        const cx = W / 2, cy = H / 2;
        const R = 48;  // outer rim radius
        const angle = (steerPct / 100) * Math.PI * 0.8; // ±144 degrees rotation

        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(angle);

        // -- Outer rim glow
        ctx.shadowColor = accentRGBA(0.3);
        ctx.shadowBlur = 8;

        // -- Outer rim (D-shape: flat bottom like F1 wheel)
        ctx.strokeStyle = accentHex;
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';

        // Top arc (from ~210° to ~330° = majority of wheel)
        ctx.beginPath();
        ctx.arc(0, 0, R, Math.PI * 1.22, Math.PI * 1.78, true); // bottom gap
        ctx.stroke();

        // Flat bottom bar
        const flatY = R * Math.cos(Math.PI * 0.22);
        const flatX = R * Math.sin(Math.PI * 0.22);
        ctx.beginPath();
        ctx.moveTo(-flatX, flatY);
        ctx.lineTo(flatX, flatY);
        ctx.stroke();

        ctx.shadowBlur = 0;

        // -- Inner grip rim
        const Ri = 38;
        ctx.strokeStyle = accentRGBA(0.35);
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(0, 0, Ri, Math.PI * 1.22, Math.PI * 1.78, true);
        ctx.stroke();

        const flatYi = Ri * Math.cos(Math.PI * 0.22);
        const flatXi = Ri * Math.sin(Math.PI * 0.22);
        ctx.beginPath();
        ctx.moveTo(-flatXi, flatYi);
        ctx.lineTo(flatXi, flatYi);
        ctx.stroke();

        // -- Center hub (rounded rectangle - manual path for compatibility)
        ctx.strokeStyle = accentRGBA(0.6);
        ctx.lineWidth = 1.5;
        const hubW = 24, hubH = 16, hr = 4;
        const hx = -hubW / 2, hy = -hubH / 2;
        ctx.beginPath();
        ctx.moveTo(hx + hr, hy);
        ctx.lineTo(hx + hubW - hr, hy);
        ctx.arcTo(hx + hubW, hy, hx + hubW, hy + hr, hr);
        ctx.lineTo(hx + hubW, hy + hubH - hr);
        ctx.arcTo(hx + hubW, hy + hubH, hx + hubW - hr, hy + hubH, hr);
        ctx.lineTo(hx + hr, hy + hubH);
        ctx.arcTo(hx, hy + hubH, hx, hy + hubH - hr, hr);
        ctx.lineTo(hx, hy + hr);
        ctx.arcTo(hx, hy, hx + hr, hy, hr);
        ctx.closePath();
        ctx.stroke();

        // -- Spokes (3 spokes: left, right, bottom-center)
        ctx.strokeStyle = accentRGBA(0.5);
        ctx.lineWidth = 3;

        // Left spoke
        ctx.beginPath();
        ctx.moveTo(-hubW / 2, 0);
        ctx.lineTo(-Ri, 0);
        ctx.stroke();

        // Right spoke
        ctx.beginPath();
        ctx.moveTo(hubW / 2, 0);
        ctx.lineTo(Ri, 0);
        ctx.stroke();

        // Bottom spoke
        ctx.beginPath();
        ctx.moveTo(0, hubH / 2);
        ctx.lineTo(0, flatYi);
        ctx.stroke();

        // -- Top center marker (12 o'clock reference on the rim)
        ctx.fillStyle = '#ff1744';
        ctx.beginPath();
        ctx.arc(0, -R, 4, 0, Math.PI * 2);
        ctx.fill();

        // -- Small buttons on hub
        ctx.fillStyle = 'rgba(255, 214, 0, 0.6)';
        ctx.beginPath();
        ctx.arc(-6, -2, 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = accentRGBA(0.6);
        ctx.beginPath();
        ctx.arc(6, -2, 2, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();

        // Static label at bottom
        ctx.fillStyle = 'rgba(255,255,255,0.4)';
        ctx.font = 'bold 9px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('STEER', cx, H - 4);
    }

    /* ======================== G-FORCE RADAR CANVAS ======================== */
    const gfTrail = []; // recent G-force points for trail effect
    const GF_TRAIL_MAX = 40;

    function drawGForceRadar(gLat, gLon) {
        const canvas = $('gforce-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        const W = 120, H = 120;
        canvas.width = W;
        canvas.height = H;
        ctx.clearRect(0, 0, W, H);

        const cx = W / 2, cy = H / 2;
        const maxG = 5; // max G to display
        const R = 48;   // radar radius = maxG

        // Store trail point
        gfTrail.push({ x: gLat, y: gLon });
        if (gfTrail.length > GF_TRAIL_MAX) gfTrail.shift();

        // -- Background circles (1G, 2G, 3G, 4G, 5G)
        for (let g = 1; g <= maxG; g++) {
            const r = (g / maxG) * R;
            ctx.beginPath();
            ctx.strokeStyle = g === 1 ? accentRGBA(0.25) : 'rgba(255,255,255,0.08)';
            ctx.lineWidth = g === 1 ? 1 : 0.5;
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            ctx.stroke();
        }

        // -- Crosshair lines
        ctx.strokeStyle = 'rgba(255,255,255,0.12)';
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(cx - R, cy);
        ctx.lineTo(cx + R, cy);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(cx, cy - R);
        ctx.lineTo(cx, cy + R);
        ctx.stroke();

        // -- Axis labels
        ctx.fillStyle = 'rgba(255,255,255,0.25)';
        ctx.font = '7px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('BRAKE', cx, cy - R - 4);
        ctx.fillText('ACCEL', cx, cy + R + 10);
        ctx.textAlign = 'left';
        ctx.fillText('L', cx - R - 8, cy + 3);
        ctx.textAlign = 'right';
        ctx.fillText('R', cx + R + 8, cy + 3);

        // G-force values: lateral = left/right (x), longitudinal = accel/brake (y inverted)
        const scale = R / maxG;

        // -- Trail (fading dots)
        for (let i = 0; i < gfTrail.length - 1; i++) {
            const pt = gfTrail[i];
            const alpha = 0.05 + (i / gfTrail.length) * 0.25;
            const px = cx + clamp(pt.x, -maxG, maxG) * scale;
            const py = cy - clamp(pt.y, -maxG, maxG) * scale;
            ctx.beginPath();
            ctx.fillStyle = accentRGBA(alpha);
            ctx.arc(px, py, 2, 0, Math.PI * 2);
            ctx.fill();
        }

        // -- Current G-force dot
        const dotX = cx + clamp(gLat, -maxG, maxG) * scale;
        const dotY = cy - clamp(gLon, -maxG, maxG) * scale;

        // Glow
        ctx.save();
        ctx.shadowColor = accentRGBA(0.8);
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.fillStyle = accentHex;
        ctx.arc(dotX, dotY, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        // Inner white dot
        ctx.beginPath();
        ctx.fillStyle = '#ffffff';
        ctx.arc(dotX, dotY, 2.5, 0, Math.PI * 2);
        ctx.fill();

        // -- G value text
        const totalG = Math.sqrt(gLat * gLat + gLon * gLon);
        ctx.fillStyle = accentHex;
        ctx.font = 'bold 11px Orbitron, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(totalG.toFixed(1) + 'G', cx, H - 4);
    }

    /* ======================== TELEMETRY TRACE ======================== */
    const traceCanvas = $('trace-canvas');
    const traceCtx = traceCanvas ? traceCanvas.getContext('2d') : null;

    function drawTrace(throttleData, brakeData, speedData) {
        if (!traceCtx || !traceCanvas) return;

        const rect = traceCanvas.parentElement.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        traceCanvas.width = rect.width * dpr;
        traceCanvas.height = rect.height * dpr;
        traceCanvas.style.width = rect.width + 'px';
        traceCanvas.style.height = rect.height + 'px';
        traceCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

        const W = rect.width;
        const H = rect.height;
        traceCtx.clearRect(0, 0, W, H);

        // Grid lines
        traceCtx.strokeStyle = 'rgba(255,255,255,0.04)';
        traceCtx.lineWidth = 1;
        for (let y = 0; y <= H; y += H / 4) {
            traceCtx.beginPath();
            traceCtx.moveTo(0, y);
            traceCtx.lineTo(W, y);
            traceCtx.stroke();
        }

        // Draw speed trace (yellow, scaled 0-350)
        if (speedData && speedData.length > 0) {
            const maxSpeed = 350;
            traceCtx.beginPath();
            traceCtx.strokeStyle = 'rgba(255,214,0,0.5)';
            traceCtx.lineWidth = 1;
            for (let i = 0; i < speedData.length; i++) {
                const x = (i / speedData.length) * W;
                const y = H - (speedData[i] / maxSpeed) * H;
                if (i === 0) traceCtx.moveTo(x, y);
                else traceCtx.lineTo(x, y);
            }
            traceCtx.stroke();
        }

        // Draw throttle trace (green)
        if (throttleData && throttleData.length > 0) {
            traceCtx.beginPath();
            traceCtx.strokeStyle = '#00e676';
            traceCtx.lineWidth = 1.5;
            for (let i = 0; i < throttleData.length; i++) {
                const x = (i / throttleData.length) * W;
                const y = H - (throttleData[i] / 100) * H;
                if (i === 0) traceCtx.moveTo(x, y);
                else traceCtx.lineTo(x, y);
            }
            traceCtx.stroke();
        }

        // Draw brake trace (red)
        if (brakeData && brakeData.length > 0) {
            traceCtx.beginPath();
            traceCtx.strokeStyle = '#e10600';
            traceCtx.lineWidth = 1.5;
            for (let i = 0; i < brakeData.length; i++) {
                const x = (i / brakeData.length) * W;
                const y = H - (brakeData[i] / 100) * H;
                if (i === 0) traceCtx.moveTo(x, y);
                else traceCtx.lineTo(x, y);
            }
            traceCtx.stroke();
        }
    }

    /* ======================== UPDATE PLAYER ======================== */
    function updatePlayer(d) {
        if (!d) return;

        // GP Banner
        const trackNames = {
            'Melbourne': 'AUSTRALIAN GRAND PRIX',
            'Shanghai': 'CHINESE GRAND PRIX',
            'Sakhir (Bahrain)': 'BAHRAIN GRAND PRIX',
            'Catalunya': 'SPANISH GRAND PRIX',
            'Monaco': 'MONACO GRAND PRIX',
            'Montreal': 'CANADIAN GRAND PRIX',
            'Silverstone': 'BRITISH GRAND PRIX',
            'Hungaroring': 'HUNGARIAN GRAND PRIX',
            'Spa': 'BELGIAN GRAND PRIX',
            'Monza': 'ITALIAN GRAND PRIX',
            'Singapore': 'SINGAPORE GRAND PRIX',
            'Suzuka': 'JAPANESE GRAND PRIX',
            'Abu Dhabi': 'ABU DHABI GRAND PRIX',
            'Texas': 'UNITED STATES GRAND PRIX',
            'Brazil': 'BRAZILIAN GRAND PRIX',
            'Austria': 'AUSTRIAN GRAND PRIX',
            'Mexico': 'MEXICAN GRAND PRIX',
            'Baku (Azerbaijan)': 'AZERBAIJAN GRAND PRIX',
            'Zandvoort': 'DUTCH GRAND PRIX',
            'Imola': 'EMILIA ROMAGNA GRAND PRIX',
            'Jeddah': 'SAUDI ARABIAN GRAND PRIX',
            'Miami': 'MIAMI GRAND PRIX',
            'Las Vegas': 'LAS VEGAS GRAND PRIX',
            'Losail': 'QATAR GRAND PRIX',
        };

        const gpName = trackNames[d.track] || d.track + ' GRAND PRIX';
        setText('gp-name', gpName);
        setText('gp-track', d.track + ' Circuit');
        setText('session-badge', d.session_type);
        setText('clock', getCurrentTimeStr());

        // Update GP flag strip based on track country
        updateGPFlag(d.track);

        // Gear highlight
        document.querySelectorAll('.gear-item').forEach(el => {
            const g = parseInt(el.dataset.g);
            el.classList.toggle('active', g === d.gear);
        });

        // Vertical bars
        const ersBar = $('ers-bar-v');
        if (ersBar) ersBar.style.height = clamp(d.ers_store) + '%';
        const brakeBar = $('brake-bar-v');
        if (brakeBar) brakeBar.style.height = clamp(d.brake) + '%';
        const thrBar = $('throttle-bar-v');
        if (thrBar) thrBar.style.height = clamp(d.throttle) + '%';

        setText('ers-pct-val', Math.round(d.ers_store) + '%');
        setText('throttle-pct-val', d.throttle + '%');

        // Steering wheel canvas
        drawSteeringWheel(d.steer);

        // G-Force radar
        drawGForceRadar(d.g_force_lat || 0, d.g_force_lon || 0);

        // Speed
        setText('speed-display', d.speed);

        // Fuel & Laps
        setText('fuel-val', d.fuel.toFixed(1) + ' L');
        const fuelLaps = d.fuel_remaining_laps;
        setText('fuel-laps-val', (fuelLaps >= 0 ? '+' : '') + fuelLaps.toFixed(2));

        // Settings
        setText('brake-bias-val', d.brake_bias.toFixed(1));
        setText('diff-val', '0%');
        setText('ers-mode-val', d.ers_mode);

        // Tyre data
        const corners = [
            { id: 'fl', wear: d.tyre_wear_fl, surf: d.tyre_temp_fl, inner: d.tyre_inner_fl, brake: d.brake_temp_fl },
            { id: 'fr', wear: d.tyre_wear_fr, surf: d.tyre_temp_fr, inner: d.tyre_inner_fr, brake: d.brake_temp_fr },
            { id: 'rl', wear: d.tyre_wear_rl, surf: d.tyre_temp_rl, inner: d.tyre_inner_rl, brake: d.brake_temp_rl },
            { id: 'rr', wear: d.tyre_wear_rr, surf: d.tyre_temp_rr, inner: d.tyre_inner_rr, brake: d.brake_temp_rr },
        ];

        for (const c of corners) {
            setText('tw-' + c.id, Math.round(c.wear) + '%');
            setText('ts-' + c.id, Math.round(c.surf) + '°');
            setText('ti-' + c.id, Math.round(c.inner) + '°');
            setText('tb-' + c.id, Math.round(c.brake) + '°');

            // Color coding
            const twEl = $('tw-' + c.id);
            if (twEl) twEl.style.color = wheelColor(c.wear);
            const tsEl = $('ts-' + c.id);
            if (tsEl) tsEl.style.color = tyreColor(c.surf);
            const tiEl = $('ti-' + c.id);
            if (tiEl) tiEl.style.color = tyreColor(c.inner);

            // Wheel SVG color
            const wheelEl = $('wheel-' + c.id);
            if (wheelEl) wheelEl.setAttribute('fill', wheelColor(c.wear));
        }

        // Live track info
        setText('lti-warnings', d.warnings || '-');
        setText('lti-penalties', d.penalties ? d.penalties + 's' : '-');
        setText('lti-ontrack', d.on_track_count || '0/0');

        // Apply team accent color
        applyTeamAccent(d.player_team);

        // Driver banner
        setText('db-pos', d.position || '--');
        setText('db-name', d.player_name);
        setText('db-team-name', d.player_team);
        setText('db-number', d.race_number || '0');

        // Team letter
        const teamAbbrs = {
            'Mercedes': 'M', 'Ferrari': 'F', 'Red Bull': 'RB', 'Williams': 'W',
            'Aston Martin': 'AM', 'Alpine': 'A', 'RB': 'RB', 'Haas': 'H',
            'McLaren': 'MC', 'Sauber': 'S'
        };
        setText('db-team-letter', teamAbbrs[d.player_team] || d.player_team?.charAt(0) || '?');

        // Telemetry traces
        drawTrace(d.throttle_trace, d.brake_trace, d.speed_trace);
    }

    /* ======================== TIMING TOWER ======================== */
    let overallBestSectors = { s1: 0, s2: 0, s3: 0 };

    function updateTimingTower(board, obs) {
        const tbody = $('tt-body');
        if (!tbody || !board || board.length === 0) return;

        if (obs) overallBestSectors = obs;
        const ob = overallBestSectors;

        function sectorClass(val, personalBest, overallBest) {
            if (!val || val <= 0) return 'tt-s-empty';
            if (overallBest > 0 && val === overallBest) return 'tt-s-purple';
            if (personalBest > 0 && val === personalBest) return 'tt-s-green';
            return 'tt-s-white';
        }

        const fragment = document.createDocumentFragment();
        for (const e of board) {
            const tr = document.createElement('tr');
            if (e.is_player) tr.classList.add('is-player');

            const s1cls = sectorClass(e.best_s1, e.best_s1, ob.s1);
            const s2cls = sectorClass(e.best_s2, e.best_s2, ob.s2);
            const s3cls = sectorClass(e.best_s3, e.best_s3, ob.s3);

            const s1txt = e.best_s1 > 0 ? fmtSectorMs(e.best_s1) : '--';
            const s2txt = e.best_s2 > 0 ? fmtSectorMs(e.best_s2) : '--';
            const s3txt = e.best_s3 > 0 ? fmtSectorMs(e.best_s3) : '--';

            const fastCls = e.is_overall_fastest ? 'tt-best-lap overall-fastest' : 'tt-best-lap';

            const driverName = e.name && e.name.includes(' ')
                ? e.short_name
                : (e.name || e.short_name);

            tr.innerHTML = `
                <td class="tt-pos">${e.position}</td>
                <td><span class="lb-team-strip" style="background:${e.team_color}"></span><span class="lb-team-abbr">${e.team_abbr}</span></td>
                <td class="tt-name">${driverName}</td>
                <td class="${s1cls}">${s1txt}</td>
                <td class="${s2cls}">${s2txt}</td>
                <td class="${s3cls}">${s3txt}</td>
                <td class="tt-last-lap">${e.last_lap}</td>
                <td class="${fastCls}">${e.fastest_lap}</td>
            `;
            fragment.appendChild(tr);
        }
        tbody.innerHTML = '';
        tbody.appendChild(fragment);
    }

    /* ======================== LEADERBOARD ======================== */
    let prevBoardStr = '';

    function updateLeaderboard(board) {
        const tbody = $('lb-body');
        if (!tbody || !board || board.length === 0) return;

        const boardStr = board.map(e => `${e.position}${e.short_name}${e.interval}`).join('|');
        if (boardStr === prevBoardStr) return;
        prevBoardStr = boardStr;

        const fragment = document.createDocumentFragment();
        for (const e of board) {
            const tr = document.createElement('tr');
            if (e.is_player) tr.classList.add('is-player');

            // ERS circle class
            let ersCls = '';
            if (e.ers_pct >= 80) ersCls = '';
            else if (e.ers_pct >= 30) ersCls = 'mid';
            else if (e.ers_pct > 0) ersCls = 'low';
            else ersCls = 'empty';

            // DRS badge class
            let drsCls = '';
            if (e.drs_active === 1) drsCls = 'active';
            else if (e.drs_allowed === 1) drsCls = 'allowed';

            // Penalty text
            const penText = e.penalties > 0 ? ` <span style="color:#e10600;font-size:11px">+${e.penalties}s</span>` : '';

            // Fastest lap highlight
            const fastCls = e.is_overall_fastest ? 'lb-fastest overall-fastest' : 'lb-fastest';

            // Tyre wear color
            const avgWear = e.avg_wear || 0;
            let wearColor = '#00e676';
            if (avgWear >= 60) wearColor = '#ff1744';
            else if (avgWear >= 35) wearColor = '#ffd600';
            const wearPct = Math.min(avgWear, 100);

            // Tyre compound dot
            const tyreCmpd = e.tyre_compound_raw || 0;
            let tyreCls = 'unknown';
            let tyreLabel = '?';
            if (tyreCmpd === 16) { tyreCls = 'soft'; tyreLabel = 'S'; }
            else if (tyreCmpd === 17) { tyreCls = 'medium'; tyreLabel = 'M'; }
            else if (tyreCmpd === 18) { tyreCls = 'hard'; tyreLabel = 'H'; }
            else if (tyreCmpd === 7) { tyreCls = 'inter'; tyreLabel = 'I'; }
            else if (tyreCmpd === 8) { tyreCls = 'wet'; tyreLabel = 'W'; }

            // Driver display name
            const driverName = e.name && e.name.includes(' ')
                ? e.short_name          // F1 AI: 3-letter abbreviation
                : (e.name || e.short_name);  // Online: full gamertag

            tr.innerHTML = `
                <td class="lb-pos">${e.position}</td>
                <td><span class="lb-team-strip" style="background:${e.team_color}"></span><span class="lb-team-abbr">${e.team_abbr}</span></td>
                <td class="lb-driver">${driverName}${penText}</td>
                <td class="lb-icon">${e.pit_status_raw > 0 ? '🔧' : ''}</td>
                <td class="lb-tyreinfo"><span class="tyre-dot ${tyreCls}"></span><span class="tyre-age-num">${e.tyre_age}L</span><span class="tyre-wear-num" style="color:${wearColor}">${avgWear}%</span></td>
                <td><span class="ers-circle ${ersCls}">${e.ers_pct}%</span></td>
                <td><span class="drs-badge-mini ${drsCls}">DRS</span></td>
                <td class="lb-interval">${e.interval}</td>
                <td class="lb-last-lap">${e.last_lap}</td>
                <td class="${fastCls}">${e.fastest_lap}</td>
            `;
            fragment.appendChild(tr);
        }
        tbody.innerHTML = '';
        tbody.appendChild(fragment);
    }

    /* ======================== WEATHER ======================== */
    function updateWeather(weather) {
        if (!weather || !weather.forecasts || weather.forecasts.length === 0) return;

        const f = weather.forecasts;

        // First card = NOW
        if (f[0]) {
            setText('wi-icon-now', f[0].weather_emoji);
            setText('wi-pct-now', f[0].rain_pct + '%');
        }
        // Find +5 min and +10 min
        for (const fc of f) {
            if (fc.time_offset === 5 || (fc.time_offset > 0 && fc.time_offset <= 5)) {
                setText('wi-icon-5', fc.weather_emoji);
                setText('wi-label-5', fc.weather.toUpperCase());
                setText('wi-pct-5', fc.rain_pct + '%');
            }
            if (fc.time_offset === 10 || (fc.time_offset > 5 && fc.time_offset <= 15)) {
                setText('wi-icon-10', fc.weather_emoji);
                setText('wi-label-10', fc.weather.toUpperCase());
                setText('wi-pct-10', fc.rain_pct + '%');
            }
        }
    }

    /* ======================== TRACK MAP ======================== */
    const trackCanvas = $('trackmap-canvas');
    const trackCtx = trackCanvas ? trackCanvas.getContext('2d') : null;
    let trackData = null;
    let currentTrackId = -1;
    let carPositions = [];
    let trackMapLoading = false;

    function resizeTrackCanvas() {
        if (!trackCanvas) return;
        const container = trackCanvas.parentElement;
        const dpr = window.devicePixelRatio || 1;
        const rect = container.getBoundingClientRect();
        trackCanvas.width = rect.width * dpr;
        trackCanvas.height = rect.height * dpr;
        trackCanvas.style.width = rect.width + 'px';
        trackCanvas.style.height = rect.height + 'px';
        trackCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
        drawTrackMap();
    }

    async function loadTrackData(trackId) {
        if (trackId === currentTrackId || trackMapLoading || trackId < 0) return;
        trackMapLoading = true;
        try {
            const resp = await fetch('/api/track/' + trackId);
            if (resp.ok) {
                trackData = await resp.json();
                currentTrackId = trackId;
                const nodata = $('trackmap-nodata');
                if (nodata) nodata.style.display = 'none';
                resizeTrackCanvas();
            } else {
                trackData = null;
            }
        } catch (e) {
            console.warn('Track load error:', e);
        }
        trackMapLoading = false;
    }

    function drawTrackMap() {
        if (!trackCtx || !trackCanvas) return;

        const W = trackCanvas.clientWidth;
        const H = trackCanvas.clientHeight;
        trackCtx.clearRect(0, 0, W, H);

        if (!trackData || !trackData.points || trackData.points.length === 0) return;

        const pts = trackData.points;
        const padding = 20;
        const availW = W - padding * 2;
        const availH = H - padding * 2;
        const size = Math.min(availW, availH);
        const offsetX = padding + (availW - size) / 2;
        const offsetY = padding + (availH - size) / 2;

        function tx(nx) { return offsetX + nx * size; }
        function tz(nz) { return offsetY + (1 - nz) * size; }

        // Track glow
        trackCtx.save();
        trackCtx.shadowColor = accentRGBA(0.2);
        trackCtx.shadowBlur = 14;
        trackCtx.lineWidth = 10;
        trackCtx.strokeStyle = accentRGBA(0.08);
        trackCtx.beginPath();
        for (let i = 0; i < pts.length; i++) {
            const x = tx(pts[i][0]);
            const y = tz(pts[i][1]);
            if (i === 0) trackCtx.moveTo(x, y);
            else trackCtx.lineTo(x, y);
        }
        trackCtx.closePath();
        trackCtx.stroke();
        trackCtx.restore();

        // Track with sector colors
        const sectorColors = [
            accentRGBA(0.6),
            'rgba(255, 214, 0, 0.6)',
            'rgba(225, 6, 0, 0.6)'
        ];

        trackCtx.lineWidth = 5;
        trackCtx.lineCap = 'round';
        trackCtx.lineJoin = 'round';

        const sectors = trackData.sectors || [];
        if (sectors.length > 0) {
            let segStart = 0;
            for (let s = 0; s < sectors.length; s++) {
                const segEnd = s + 1 < sectors.length ? sectors[s + 1].index : pts.length;
                const color = sectorColors[sectors[s].sector % 3];
                trackCtx.beginPath();
                trackCtx.strokeStyle = color;
                for (let i = segStart; i < segEnd && i < pts.length; i++) {
                    const x = tx(pts[i][0]);
                    const y = tz(pts[i][1]);
                    if (i === segStart) trackCtx.moveTo(x, y);
                    else trackCtx.lineTo(x, y);
                }
                trackCtx.stroke();
                segStart = segEnd > 0 ? segEnd - 1 : segEnd;
            }
        } else {
            trackCtx.beginPath();
            trackCtx.strokeStyle = accentRGBA(0.5);
            for (let i = 0; i < pts.length; i++) {
                const x = tx(pts[i][0]);
                const y = tz(pts[i][1]);
                if (i === 0) trackCtx.moveTo(x, y);
                else trackCtx.lineTo(x, y);
            }
            trackCtx.closePath();
            trackCtx.stroke();
        }

        // Close circuit
        trackCtx.beginPath();
        trackCtx.strokeStyle = sectorColors[0];
        trackCtx.lineWidth = 5;
        trackCtx.moveTo(tx(pts[pts.length - 1][0]), tz(pts[pts.length - 1][1]));
        trackCtx.lineTo(tx(pts[0][0]), tz(pts[0][1]));
        trackCtx.stroke();

        // Draw car positions
        if (!carPositions || carPositions.length === 0) return;

        // Non-player cars
        for (const car of carPositions) {
            if (car.is_player || car.pit > 0) continue;
            const cx = tx(car.x);
            const cy = tz(car.z);

            trackCtx.beginPath();
            trackCtx.fillStyle = 'rgba(0,0,0,0.5)';
            trackCtx.arc(cx, cy, 13, 0, Math.PI * 2);
            trackCtx.fill();

            trackCtx.beginPath();
            trackCtx.fillStyle = car.color || '#ffffff';
            trackCtx.arc(cx, cy, 10, 0, Math.PI * 2);
            trackCtx.fill();

            trackCtx.fillStyle = '#000';
            trackCtx.font = 'bold 11px Inter, sans-serif';
            trackCtx.textAlign = 'center';
            trackCtx.textBaseline = 'middle';
            trackCtx.fillText(car.pos, cx, cy + 0.5);
        }

        // Player car (more prominent)
        for (const car of carPositions) {
            if (!car.is_player) continue;
            const cx = tx(car.x);
            const cy = tz(car.z);

            // Glow
            trackCtx.save();
            trackCtx.shadowColor = accentRGBA(0.6);
            trackCtx.shadowBlur = 12;
            trackCtx.beginPath();
            trackCtx.fillStyle = accentRGBA(0.2);
            trackCtx.arc(cx, cy, 22, 0, Math.PI * 2);
            trackCtx.fill();
            trackCtx.restore();

            trackCtx.beginPath();
            trackCtx.fillStyle = 'rgba(0,0,0,0.6)';
            trackCtx.arc(cx, cy, 16, 0, Math.PI * 2);
            trackCtx.fill();

            trackCtx.beginPath();
            trackCtx.fillStyle = car.color || accentHex;
            trackCtx.strokeStyle = '#ffffff';
            trackCtx.lineWidth = 2.5;
            trackCtx.arc(cx, cy, 13, 0, Math.PI * 2);
            trackCtx.fill();
            trackCtx.stroke();

            trackCtx.fillStyle = '#fff';
            trackCtx.font = 'bold 12px Inter, sans-serif';
            trackCtx.textAlign = 'center';
            trackCtx.textBaseline = 'middle';
            trackCtx.fillText('P' + car.pos, cx, cy + 0.5);

            // Name label
            trackCtx.fillStyle = accentHex;
            trackCtx.font = 'bold 14px Inter, sans-serif';
            trackCtx.fillText(car.name, cx, cy - 19);
        }
    }

    function updateCarPositions(data) {
        if (!data) return;
        if (data.track_id !== currentTrackId && data.track_id >= 0) {
            loadTrackData(data.track_id);
        }
        carPositions = data.cars || [];
        drawTrackMap();
    }

    // Resize handlers
    window.addEventListener('resize', () => {
        if (trackData) resizeTrackCanvas();
    });
    if (trackCanvas && window.ResizeObserver) {
        const ro = new ResizeObserver(() => {
            if (trackData) resizeTrackCanvas();
        });
        ro.observe(trackCanvas.parentElement);
    }

    /* ======================== MAIN LISTENER ======================== */
    socket.on('telemetry_update', (payload) => {
        if (payload.player) updatePlayer(payload.player);
        if (payload.leaderboard) {
            updateLeaderboard(payload.leaderboard);
            updateTimingTower(payload.leaderboard, payload.overall_best_sectors);
        }
        if (payload.weather) updateWeather(payload.weather);
        if (payload.car_positions) updateCarPositions(payload.car_positions);
    });

    // Clock update
    setInterval(() => setText('clock', getCurrentTimeStr()), 10000);

    console.log('%c🏎 F1 25 Broadcast Engineer Display', 'color:' + accentHex + ';font-weight:bold;font-size:14px');
})();
