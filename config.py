import os

# ==========================================
# SYSTEM OPERATING MODE
# ==========================================
# Options: 'vehicle' (Toll Plaza / FASTag) or 'people' (Counter Queue)
DEFAULT_MODE = "vehicle"

# ==========================================
# CLEARANCE / SERVICE TIME WEIGHTS (SECONDS)
# ==========================================
# Based on Passenger Car Unit (PCU) equivalents in transportation engineering
SERVICE_TIMES_SEC = {
    # Vehicle classes
    "car": 15,
    "bus": 35,
    "truck": 50,
    "motorbike": 8,
    "ambulance": 0,  # Emergency vehicle: Instant green corridor preemption
    
    # People class (for counter queue mode)
    "person": 40
}

# ==========================================
# PENALTY & ENFORCEMENT CONFIGURATION
# ==========================================
BASE_TOLL_FARE = 90          # Base toll charge (INR)
VIOLATION_PENALTY = 500      # Fine for queue-cutting / hazardous lane breach (INR)
PENALTY_CODE = "SEC-177-MV"  # Indian Motor Vehicles Act lane discipline violation code

# ==========================================
# ADAPTIVE CENTROID TRACKER PARAMETERS
# ==========================================
# allowed_distance = base_distance + (missed_frames * per_frame_motion_allowance)
TRACKER_BASE_DISTANCE = 70.0
TRACKER_PER_FRAME_ALLOWANCE = 12.0
MAX_MISSED_FRAMES = 25

# ==========================================
# DYNAMIC CORRIDOR & VIOLATION PARAMETERS
# ==========================================
# Minimum active objects required before violation detection turns ON
# (Low-occupancy safety guard: avoids false alarms when queue is sparse)
MIN_OBJECTS_FOR_ENFORCEMENT = 3

# Pixel tolerance around the dynamic back-edge to qualify as legitimate queue entry
BACK_EDGE_TOLERANCE_PX = 85

# Front service zone boundary (fraction of screen height from top or counter line)
# Queue flows from bottom (entry) to top (counter/toll barrier) by default
SERVICE_BARRIER_Y_RATIO = 0.20   # Top 20% is the service / boom-barrier zone

# Default lateral corridor boundaries (normalized X coordinates 0.0 - 1.0)
DEFAULT_CORRIDOR_X_MIN = 0.20
DEFAULT_CORRIDOR_X_MAX = 0.80

# ==========================================
# SENSOR INTEGRATION (ESP32)
# ==========================================
ULTRASONIC_PRESENCE_THRESHOLD_CM = 150  # Distance < 1.5m means vehicle/person is at barrier

# ==========================================
# STORAGE & LOGGING PATHS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERTS_DIR = os.path.join(BASE_DIR, "alerts")
MODELS_DIR = os.path.join(BASE_DIR, "models")
LIVE_STATE_FILE = os.path.join(BASE_DIR, "live_state.json")
VIOLATIONS_FILE = os.path.join(BASE_DIR, "violations.json")

# Ensure required directories exist
os.makedirs(ALERTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
