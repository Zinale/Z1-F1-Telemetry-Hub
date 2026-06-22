"""
F1 25 Telemetry - Track Map Loader
Carica e processa i file delle mappe dei circuiti per la visualizzazione real-time.
Usa lap_distance per posizionare le auto sulla mappa (indipendente dalla versione del gioco).
"""

import os
import bisect

# Relative path to the 'tracks' directory containing track files
TRACKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracks')

# Mapping: track_id -> track file name
TRACK_FILE_MAP = {
    0:  'melbourne_2020_racingline.txt',
    2:  'shanghai_2020_racingline.txt',
    3:  'sakhir_2020_racingline.txt',
    4:  'catalunya_2020_racingline.txt',
    5:  'monaco_2020_racingline.txt',
    6:  'montreal_2020_racingline.txt',
    7:  'silverstone_2020_racingline.txt',
    9:  'hungaroring_2020_racingline.txt',
    10: 'spa_2020_racingline.txt',
    11: 'monza_2020_racingline.txt',
    12: 'singapore_2020_racingline.txt',
    13: 'suzuka_2020_racingline.txt',
    14: 'abu_dhabi_2020_racingline.txt',
    15: 'texas_2020_racingline.txt',
    16: 'brazil_2020_racingline.txt',
    17: 'austria_2020_racingline.txt',
    19: 'mexico_2020_racingline.txt',
    20: 'baku_2020_racingline.txt',
    26: 'zandvoort_2020_racingline.txt',
    27: 'imola_2020_racingline.txt',
    29: 'jeddah_2020_racingline.txt',
    30: 'miami_2020_racingline.txt',
    31: 'Las Vegas_2020_racingline.txt',
    32: 'losail_2020_racingline.txt',
    # Reversed circuits use the same map
    39: 'silverstone_2020_racingline.txt',
    40: 'austria_2020_racingline.txt',
    41: 'zandvoort_2020_racingline.txt',
}


# Global cache for loaded tracks to avoid reloading from disk
_track_cache = {}


def _parse_track_file(filepath):
    """
    Parsa un file tracciato e restituisce una lista di punti (dist, x, z, sector).
    Il formato è: dist, pos_z, pos_x, pos_y, drs, sector
    """
    points = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Skip the first 2 lines (file header and column header)
        for line in lines[2:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) >= 6:
                try:
                    dist = float(parts[0])
                    pos_z = float(parts[1])
                    pos_x = float(parts[2])
                    sector = int(parts[5])
                    points.append((dist, pos_x, pos_z, sector))
                except (ValueError, IndexError):
                    continue
    except Exception as e:
        print(f"Error loading track file {filepath}: {e}")

    return points


def _downsample(points, max_points=700):
    """Riduce il numero di punti mantenendo la forma del tracciato."""
    if len(points) <= max_points:
        return points
    step = len(points) / max_points
    result = []
    for i in range(max_points):
        idx = int(i * step)
        result.append(points[idx])
    # Ensure the last point is included to close the circuit
    if result[-1] != points[-1]:
        result.append(points[-1])
    return result


def _normalize_points(points):
    """
    Normalizes x,z coordinates to the 0-1 range while maintaining proportions.
    Returns (normalized_points, track_length).
    Each point: (dist, nx, nz, sector)
    """
    if not points:
        return [], 0

    xs = [p[1] for p in points]
    zs = [p[2] for p in points]

    min_x, max_x = min(xs), max(xs)
    min_z, max_z = min(zs), max(zs)

    range_x = max_x - min_x
    range_z = max_z - min_z

    if range_x == 0 and range_z == 0:
        return [], 0

    # Maintain aspect ratio: use the largest range as reference
    max_range = max(range_x, range_z) if max(range_x, range_z) > 0 else 1

    # Center in the normalized range
    offset_x = (max_range - range_x) / 2
    offset_z = (max_range - range_z) / 2

    normalized = []
    for dist, x, z, sector in points:
        nx = (x - min_x + offset_x) / max_range
        nz = (z - min_z + offset_z) / max_range
        normalized.append((dist, nx, nz, sector))

    # Total track length (distance of the last point)
    track_length = points[-1][0] if points else 0

    return normalized, track_length


def load_track(track_id):
    """
    Loads and returns track data for a given track_id.
    Uses cache to avoid reloading.
    """
    if track_id in _track_cache:
        return _track_cache[track_id]

    filename = TRACK_FILE_MAP.get(track_id)
    if not filename:
        return None

    filepath = os.path.join(TRACKS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"Track file not found: {filepath}")
        return None

    raw_points = _parse_track_file(filepath)
    if not raw_points:
        return None

    # Downsample for performance
    sampled = _downsample(raw_points, max_points=700)

    # Normalize
    normalized, track_length = _normalize_points(sampled)
    if not normalized:
        return None

    # Find sector change points
    sector_starts = []
    prev_sector = -1
    for i, (_, _, _, sector) in enumerate(normalized):
        if sector != prev_sector:
            sector_starts.append({'index': i, 'sector': sector})
            prev_sector = sector

    # Lookup table for distance -> normalized position
    # Sorted by distance, used with bisect for fast lookup
    dist_table = [(p[0], p[1], p[2]) for p in normalized]  # (dist, nx, nz)

    track_data = {
        'points': [(round(nx, 5), round(nz, 5)) for _, nx, nz, _ in normalized],
        'sectors': sector_starts,
        'dist_table': dist_table,  # for mapping lap_distance -> position
        'track_length': track_length,
    }

    _track_cache[track_id] = track_data
    print(f"Track loaded: ID={track_id}, {len(normalized)} points, length={track_length:.0f}m")
    return track_data


def dist_to_position(lap_distance, track_data):
    """
    Converts lap_distance (meters traveled in the lap) to normalized coordinates (nx, nz).
    Uses linear interpolation between the two closest points in the distance table.
    """
    dist_table = track_data.get('dist_table', [])
    if not dist_table:
        return 0.5, 0.5

    track_len = track_data.get('track_length', 0)
    if track_len <= 0:
        return 0.5, 0.5

    # Handle negative lap_distance or values beyond track length
    # The game can provide negative values (before the finish line) or > track_length
    d = lap_distance % track_len if track_len > 0 else 0

    # Find the point in the dist_table using bisect
    dists = [p[0] for p in dist_table]
    idx = bisect.bisect_right(dists, d)

    if idx == 0:
        return dist_table[0][1], dist_table[0][2]
    if idx >= len(dist_table):
        return dist_table[-1][1], dist_table[-1][2]

    # Linear interpolation between idx-1 and idx
    d0, nx0, nz0 = dist_table[idx - 1]
    d1, nx1, nz1 = dist_table[idx]

    if d1 - d0 == 0:
        return nx0, nz0

    t = (d - d0) / (d1 - d0)
    nx = nx0 + t * (nx1 - nx0)
    nz = nz0 + t * (nz1 - nz0)
    return round(nx, 5), round(nz, 5)


def get_track_json(track_id):
    """
    Returns track data in a JSON-friendly format.
    Only normalized coordinates and aspect ratio info for the frontend.
    """
    track = load_track(track_id)
    if not track:
        return None

    return {
        'track_id': track_id,
        'points': track['points'],  # already [(nx, nz), ...]
        'sectors': track['sectors'],
    }


# Pre-load all available tracks at module import
def preload_all_tracks():
    """Pre-load all tracks into cache."""
    loaded = 0
    for track_id in TRACK_FILE_MAP:
        result = load_track(track_id)
        if result:
            loaded += 1
    print(f" Pre-loaded {loaded}/{len(TRACK_FILE_MAP)} tracks")


if __name__ == '__main__':
    preload_all_tracks()
    # Test: show info about Abu Dhabi
    ad = load_track(14)
    if ad:
        print(f"Abu Dhabi: {len(ad['points'])} points, length={ad['track_length']:.0f}m")
        # Test mapping distance
        for d in [0, 1000, 2500, 4000]:
            nx, nz = dist_to_position(d, ad)
            print(f"  dist={d}m -> nx={nx:.4f}, nz={nz:.4f}")
