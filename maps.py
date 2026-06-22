"""
F1 25 Telemetry - Lookup Maps & Constants
Tutte le mappe di traduzione per i pacchetti UDP F1 25
"""

# ============================================================
# PACKET IDS
# ============================================================
PACKET_IDS = {
    0: "Motion",
    1: "Session",
    2: "Lap Data",
    3: "Event",
    4: "Participants",
    5: "Car Setups",
    6: "Car Telemetry",
    7: "Car Status",
    8: "Final Classification",
    9: "Lobby Info",
    10: "Car Damage",
    11: "Session History",
    12: "Tyre Sets",
    13: "Motion Ex",
    14: "Time Trial",
    15: "Lap Positions"
}

# ============================================================
# TEAMS
# ============================================================
TEAM_IDS_MAP = {
    0: "Mercedes", 1: "Ferrari", 2: "Red Bull", 3: "Williams",
    4: "Aston Martin", 5: "Alpine", 6: "RB", 7: "Haas",
    8: "McLaren", 9: "Sauber",
    41: "F1 Generic", 104: "F1 Custom Team", 129: "Konnersport",
    142: "APXGP '24", 154: "APXGP '25"
}

TEAM_COLORS = {
    0: "#00d2be",   # Mercedes - Teal
    1: "#dc0000",   # Ferrari - Red
    2: "#3671C6",   # Red Bull - Blue
    3: "#64C4FF",   # Williams - Light Blue
    4: "#358C75",   # Aston Martin - Green
    5: "#0090FF",   # Alpine - Blue
    6: "#6692FF",   # RB - Purple-Blue
    7: "#B6BABD",   # Haas - Grey
    8: "#FF8700",   # McLaren - Orange
    9: "#52E252",   # Sauber - Green
}

# ============================================================
# DRIVERS
# ============================================================
DRIVER_IDS_MAP = {
    0: "Carlos Sainz", 2: "Daniel Ricciardo", 3: "Fernando Alonso",
    4: "Felipe Massa", 7: "Lewis Hamilton", 9: "Max Verstappen",
    10: "Nico Hulkenberg", 11: "Kevin Magnussen", 14: "Sergio Perez",
    15: "Valtteri Bottas", 17: "Esteban Ocon", 19: "Lance Stroll",
    20: "Arron Barnes", 21: "Martin Giles", 22: "Alex Murray",
    23: "Lucas Roth", 24: "Igor Correia", 25: "Sophie Levasseur",
    26: "Jonas Schiffer", 27: "Alain Forest", 28: "Jay Letourneau",
    29: "Esto Saari", 30: "Yasar Atiyeh", 31: "Callisto Calabresi",
    32: "Naota Izum", 33: "Howard Clarke", 34: "Lars Kaufmann",
    35: "Marie Laursen", 36: "Flavio Nieves", 38: "Klimek Michalski",
    39: "Santiago Moreno", 40: "Benjamin Coppens", 41: "Noah Visser",
    50: "George Russell", 54: "Lando Norris", 58: "Charles Leclerc",
    59: "Pierre Gasly", 62: "Alexander Albon", 70: "Rashid Nair",
    71: "Jack Tremblay", 77: "Ayrton Senna", 80: "Guanyu Zhou",
    83: "Juan Manuel Correa", 90: "Michael Schumacher", 94: "Yuki Tsunoda",
    102: "Aidan Jackson", 109: "Jenson Button", 110: "David Coulthard",
    112: "Oscar Piastri", 113: "Liam Lawson", 116: "Richard Verschoor",
    123: "Enzo Fittipaldi", 125: "Mark Webber", 126: "Jacque Villeneuve",
    127: "Callie Mayer", 132: "Logan Sargeant", 136: "Jack Doohan",
    137: "Amaury Cordeel", 138: "Dennis Hauger", 145: "Zane Maloney",
    146: "Victor Martins", 147: "Oliver Bearman", 148: "Jack Crawford",
    149: "Isaack Hadjar", 152: "Roman Stanek", 153: "Kush Maini",
    156: "Brendon Leigh", 157: "David Tonizza", 158: "Jarno Opmeer",
    159: "Lucas Blakeley", 160: "Paul Aron", 161: "Gabriel Bortoleto",
    162: "Franco Colapinto", 163: "Taylor Barnard", 164: "Joshua Durksen",
    165: "Andrea Kimi Antonelli", 166: "Ritomo Miyata",
    167: "Rafael Villagómez", 168: "Zak O'Sullivan", 169: "Pepe Martí",
    170: "Sonny Hayes", 171: "Joshua Pearce", 172: "Callum Voisin",
    173: "Matias Zagazeta", 174: "Nikola Tsolov", 175: "Tim Tramnitz",
    185: "Luca Cortez"
}

# ============================================================
# WEATHER
# ============================================================
WEATHER_MAP = {
    0: "Clear", 1: "Light Cloud", 2: "Overcast",
    3: "Light Rain", 4: "Heavy Rain", 5: "Storm"
}

WEATHER_EMOJI = {
    0: "☀️", 1: "🌤️", 2: "☁️",
    3: "🌧️", 4: "🌧️", 5: "⛈️"
}

# ============================================================
# SESSION
# ============================================================
SESSION_TYPE_MAP = {
    0: "Unknown", 1: "FP1", 2: "FP2", 3: "FP3",
    4: "Short Practice", 5: "Q1", 6: "Q2", 7: "Q3",
    8: "Short Qualifying", 9: "One-Shot Qualifying",
    10: "Sprint Shootout 1", 11: "Sprint Shootout 2",
    12: "Sprint Shootout 3", 13: "Short Sprint Shootout",
    14: "One Shot Sprint Shootout", 15: "Race", 16: "Race 2",
    17: "Race 3", 18: "Time Trial"
}

# ============================================================
# TRACKS
# ============================================================
TRACK_IDS_MAP = {
    0: "Melbourne", 2: "Shanghai", 3: "Sakhir (Bahrain)",
    4: "Catalunya", 5: "Monaco", 6: "Montreal",
    7: "Silverstone", 9: "Hungaroring", 10: "Spa",
    11: "Monza", 12: "Singapore", 13: "Suzuka",
    14: "Abu Dhabi", 15: "Texas", 16: "Brazil",
    17: "Austria", 19: "Mexico", 20: "Baku (Azerbaijan)",
    26: "Zandvoort", 27: "Imola", 29: "Jeddah",
    30: "Miami", 31: "Las Vegas", 32: "Losail",
    39: "Silverstone Reverse", 40: "Austria Reverse",
    41: "Zandvoort Reverse"
}

# ============================================================
# FORMULA
# ============================================================
FORMULA_MAP = {
    0: "F1 Modern", 1: "F1 Classic", 2: "F2",
    3: "F1 Generic", 4: "Beta", 6: "Esports",
    8: "F1 World", 9: "F1 Elimination"
}

# ============================================================
# SAFETY CAR
# ============================================================
SAFETY_CAR_MAP = {
    0: "No Safety Car", 1: "Full", 2: "Virtual", 3: "Formation Lap"
}

# ============================================================
# FLAGS
# ============================================================
FLAG_MAP = {
    -1: "Invalid/Unknown", 0: "None",
    1: "Green", 2: "Blue", 3: "Yellow"
}

# ============================================================
# TYRES
# ============================================================
ACTUAL_TYRE_COMPOUND_MAP = {
    16: "C5", 17: "C4", 18: "C3", 19: "C2", 20: "C1",
    21: "C0", 22: "C6", 7: "Inter", 8: "Wet",
    9: "F1 Classic Dry", 10: "F1 Classic Wet",
    11: "F2 Super Soft", 12: "F2 Soft", 13: "F2 Medium",
    14: "F2 Hard", 15: "F2 Wet"
}

VISUAL_TYRE_MAP = {
    16: "🔴 Soft", 17: "🟡 Medium", 18: "⚪ Hard",
    7: "🟢 Inter", 8: "🔵 Wet",
    19: "F2 Super Soft", 20: "F2 Soft",
    21: "F2 Medium", 22: "F2 Hard",
    0: "-", 255: "-"
}

# ============================================================
# PIT STATUS
# ============================================================
PIT_STATUS_MAP = {
    0: "None", 1: "Pitting", 2: "In Pit Area"
}

# ============================================================
# SECTORS
# ============================================================
SECTOR_MAP = {
    0: "Sector 1", 1: "Sector 2", 2: "Sector 3"
}

# ============================================================
# DRIVER STATUS
# ============================================================
DRIVER_STATUS_MAP = {
    0: "In Garage", 1: "Flying Lap", 2: "In Lap",
    3: "Out Lap", 4: "On Track"
}

# ============================================================
# RESULT STATUS
# ============================================================
RESULT_STATUS_MAP = {
    0: "Invalid", 1: "Inactive", 2: "Active",
    3: "Finished", 4: "Did Not Finish", 5: "Disqualified",
    6: "Not Classified", 7: "Retired"
}

RESULT_REASON_MAP = {
    0: "Invalid", 1: "Retired", 2: "Finished",
    3: "Terminal Damage", 4: "Inactive",
    5: "Not Enough Laps", 6: "Black Flagged",
    7: "Red Flagged", 8: "Mechanical Failure",
    9: "Session Skipped", 10: "Session Simulated"
}

# ============================================================
# CAR CONTROLS
# ============================================================
TRACTION_CONTROL_MAP = {0: "Off", 1: "Medium", 2: "Full"}

FUEL_MIX_MAP = {0: "Lean", 1: "Standard", 2: "Rich", 3: "Max"}

ERS_DEPLOY_MODE_MAP = {0: "None", 1: "Medium", 2: "Hotlap", 3: "Overtake"}

DRS_ALLOWED_MAP = {0: "Not Allowed", 1: "Allowed"}
DRS_ACTIVATION_MAP = {0: "DRS Not Available", 1: "DRS Available"}
DRS_STATUS_MAP = {0: "Off", 1: "On"}
ANTI_LOCK_BRAKES_MAP = {0: "Off", 1: "On"}

# ============================================================
# SURFACE TYPES
# ============================================================
SURFACE_TYPE_MAP = {
    0: "Tarmac", 1: "Rumble Strip", 2: "Concrete",
    3: "Rock", 4: "Gravel", 5: "Mud", 6: "Sand",
    7: "Grass", 8: "Water", 9: "Cobblestone",
    10: "Metal", 11: "Ridged"
}

# ============================================================
# PENALTIES
# ============================================================
PENALTY_TYPE_MAP = {
    0: "Drive Through", 1: "Stop Go", 2: "Grid Penalty",
    3: "Penalty Reminder", 4: "Time Penalty", 5: "Warning",
    6: "Disqualified", 7: "Removed From Formation Lap",
    8: "Parked Too Long Timer", 9: "Tyre Regulations",
    10: "This Lap Invalidated", 11: "This And Next Lap Invalidated",
    12: "This Lap Invalidated without reason",
    13: "This And Next Lap Invalidated without reason",
    14: "This And Previous Lap Invalidated",
    15: "This And Previous Lap Invalidated without reason",
    16: "Retired", 17: "Black Flag Timer"
}

INFRINGEMENT_TYPE_MAP = {
    0: "Blocking By Slow Driving", 1: "Blocking By Wrong Way Driving",
    2: "Reversing Off Start Line", 3: "Big Collision",
    4: "Small Collision",
    5: "Collision Failed To Hand Back Position Single",
    6: "Collision Failed To Hand Back Position Multiple",
    7: "Corner Cutting Gained Time",
    8: "Corner Cutting Overtake Single",
    9: "Corner Cutting Overtake Multiple",
    10: "Crossed Pit Exit Lane", 11: "Ignoring Blue Flags",
    12: "Ignoring Yellow Flags", 13: "Ignoring Drive Through",
    14: "Too Many Drive Throughs",
    15: "Drive Through Reminder Serve Within N Laps",
    16: "Drive Through Reminder Serve This Lap",
    17: "Pit Lane Speeding", 18: "Parked For Too Long",
    19: "Ignoring Tyre Regulations", 20: "Too Many Penalties",
    21: "Multiple Warnings", 22: "Approaching Disqualification",
    23: "Tyre Regulations Select Single",
    24: "Tyre Regulations Select Multiple",
    25: "Lap Invalidated Corner Cutting",
    26: "Lap Invalidated Running Wide",
    27: "Corner Cutting Ran Wide Gained Time Minor",
    28: "Corner Cutting Ran Wide Gained Time Significant",
    29: "Corner Cutting Ran Wide Gained Time Extreme",
    30: "Lap Invalidated Wall Riding", 31: "Lap Invalidated Flashback Used",
    32: "Lap Invalidated Reset To Track", 33: "Blocking Prevented Overtake",
    34: "Jumped Start", 35: "Safety Car To Car Collision",
    36: "Safety Car Illegal Overtake",
    37: "Safety Car Exceeding Allowed Pace",
    38: "Virtual Safety Car Exceeding Allowed Pace",
    39: "Formation Lap Below Allowed Speed",
    40: "Formation Lap Parking", 41: "Retired Mechanical Failure",
    42: "Retired Terminally Damaged",
    43: "Safety Car Falling Too Far Back", 44: "Black Flag Timer",
    45: "Unserved Stop Go Penalty", 46: "Unserved Drive Through Penalty",
    47: "Engine Component Change", 48: "Gearbox Change",
    49: "Parc Fermé Change", 50: "League Grid Penalty",
    51: "Retry Penalty", 52: "Illegal Time Gain",
    53: "Mandatory Pitstop", 54: "Attribute assigned"
}

# ============================================================
# GAME MODES & RULES
# ============================================================
GAME_MODE_MAP = {
    3: "Grand Prix", 4: "Grand Prix '23", 5: "Time Trial",
    6: "Splitscreen", 7: "Online Custom", 15: "Online Weekly Event",
    27: "My Team Career '25", 28: "Driver Career '25",
    29: "Career '25 Online", 30: "Challenge Career '25",
    75: "Story Mode (APXGP)", 127: "Benchmark"
}

RULESET_MAP = {
    0: "Practice & Qualifying", 1: "Race",
    2: "Time Trial", 13: "Elimination"
}

SESSION_LENGTH_MAP = {
    0: "None", 2: "Very Short", 3: "Short",
    4: "Medium", 5: "Medium Long", 6: "Long", 7: "Full"
}

# ============================================================
# PLATFORM
# ============================================================
PLATFORM_MAP = {
    1: "Steam", 3: "PlayStation", 4: "Xbox",
    6: "Origin", 255: "Unknown"
}

# ============================================================
# NATIONALITY
# ============================================================
NATIONALITY_MAP = {
    1: "American", 2: "Argentinian", 3: "Australian",
    4: "Austrian", 5: "Azerbaijani", 6: "Bahraini",
    7: "Belgian", 8: "Bolivian", 9: "Brazilian",
    10: "British", 11: "Bulgarian", 12: "Cameroonian",
    13: "Canadian", 14: "Chilean", 15: "Chinese",
    16: "Colombian", 17: "Costa Rican", 18: "Croatian",
    19: "Cypriot", 20: "Czech", 21: "Danish",
    22: "Dutch", 23: "Ecuadorian", 24: "English",
    25: "Emirian", 26: "Estonian", 27: "Finnish",
    28: "French", 29: "German", 30: "Ghanaian",
    31: "Greek", 32: "Guatemalan", 33: "Honduran",
    34: "Hong Konger", 35: "Hungarian", 36: "Icelander",
    37: "Indian", 38: "Indonesian", 39: "Irish",
    40: "Israeli", 41: "Italian", 42: "Jamaican",
    43: "Japanese", 44: "Jordanian", 45: "Kuwaiti",
    46: "Latvian", 47: "Lebanese", 48: "Lithuanian",
    49: "Luxembourger", 50: "Malaysian", 51: "Maltese",
    52: "Mexican", 53: "Monegasque", 54: "New Zealander",
    55: "Nicaraguan", 56: "Northern Irish", 57: "Norwegian",
    58: "Omani", 59: "Pakistani", 60: "Panamanian",
    61: "Paraguayan", 62: "Peruvian", 63: "Polish",
    64: "Portuguese", 65: "Qatari", 66: "Romanian",
    67: "Russian", 68: "Salvadoran", 69: "Saudi",
    70: "Scottish", 71: "Serbian", 72: "Singaporean",
    73: "Slovakian", 74: "Slovenian", 75: "South Korean",
    76: "South African", 77: "Spanish", 78: "Swedish",
    79: "Swiss", 80: "Thai", 81: "Turkish",
    82: "Uruguayan", 83: "Ukrainian", 84: "Venezuelan",
    85: "Barbadian", 86: "Welsh", 87: "Vietnamese",
    88: "Algerian", 89: "Bosnian", 90: "Filipino"
}

# ============================================================
# GEARBOX ASSIST
# ============================================================
GEARBOX_ASSIST_MAP = {
    1: "Manual", 2: "Manual & Suggested Gear", 3: "Auto"
}

# ============================================================
# EVENT CODES
# ============================================================
EVENT_CODES = {
    "SSTA": "Session Started", "SEND": "Session Ended",
    "FTLP": "Fastest Lap", "RTMT": "Retirement",
    "DRSE": "DRS Enabled", "DRSD": "DRS Disabled",
    "TMPT": "Team Mate In Pits", "CHQF": "Chequered Flag",
    "RCWN": "Race Winner", "PENA": "Penalty Issued",
    "SPTP": "Speed Trap Triggered", "STLG": "Start Lights",
    "LGOT": "Lights Out", "DTSV": "Drive Through Served",
    "SGSV": "Stop Go Served", "FLBK": "Flashback",
    "BUTN": "Button Status", "RDFL": "Red Flag",
    "OVTK": "Overtake", "SCAR": "Safety Car",
    "COLL": "Collision"
}

EVENT_EMOJIS = {
    "SSTA": "🟢", "SEND": "🏁", "FTLP": "⚡",
    "RTMT": "🚫", "DRSE": "🟩", "DRSD": "🟥",
    "TMPT": "🔧", "CHQF": "🏁", "RCWN": "🏆",
    "PENA": "⚠️", "SPTP": "💨", "STLG": "🚦",
    "LGOT": "🚦", "DTSV": "🔄", "SGSV": "🛑",
    "FLBK": "⏪", "RDFL": "🟥", "OVTK": "🔀",
    "SCAR": "🚗", "COLL": "💥"
}
