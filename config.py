import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMERA_CONFIG_FILE = os.path.join(BASE_DIR, "camera_config.json")

# ==========================================
# SYSTEM OPERATING MODE
# ==========================================
# Options: 'vehicle' (Toll Plaza / FASTag) or 'people' (Counter Queue)
DEFAULT_MODE = "vehicle"

# ==========================================
# CAMERA SOURCE CONFIGURATION
# ==========================================
# Default fallback IP or 0 for built-in laptop webcam
DEFAULT_CAMERA_SOURCE = "http://10.200.1.248:8080/video"

def format_camera_source(raw_input):
    """Sanitizes user input into a valid OpenCV camera source URL or integer index."""
    if raw_input is None:
        return DEFAULT_CAMERA_SOURCE
    cleaned = str(raw_input).strip()
    if cleaned.isdigit():
        return int(cleaned)
    if not (cleaned.startswith("http://") or cleaned.startswith("https://") or cleaned.startswith("rtsp://")):
        cleaned = "http://" + cleaned
    if (":8080" in cleaned or ":4747" in cleaned) and not cleaned.endswith("/video"):
        cleaned = cleaned.rstrip("/") + "/video"
    return cleaned

def get_active_camera_source():
    """Returns the dynamically configured camera source if set, otherwise default."""
    if os.path.exists(CAMERA_CONFIG_FILE):
        try:
            with open(CAMERA_CONFIG_FILE, "r") as f:
                data = json.load(f)
                return format_camera_source(data.get("camera_source", DEFAULT_CAMERA_SOURCE))
        except Exception:
            pass
    return format_camera_source(DEFAULT_CAMERA_SOURCE)

def set_active_camera_source(new_source):
    """Saves dynamic camera source to camera_config.json."""
    formatted = format_camera_source(new_source)
    try:
        with open(CAMERA_CONFIG_FILE, "w") as f:
            json.dump({"camera_source": formatted}, f, indent=2)
    except Exception:
        pass
    return formatted

CAMERA_SOURCE = get_active_camera_source()
CAMERA_FLIP_180 = True   # Enabled for 3D model gantry inverted phone mount

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
MIN_OBJECTS_FOR_ENFORCEMENT = 1

# Pixel tolerance around the dynamic back-edge to qualify as legitimate queue entry
BACK_EDGE_TOLERANCE_PX = 85

# Front service zone boundary (fraction of screen height from top or counter line)
# Queue flows from bottom (entry) to top (counter/toll barrier) by default
SERVICE_BARRIER_Y_RATIO = 0.20   # Top 20% is the service / boom-barrier zone

# Default lateral corridor boundaries (normalized X coordinates 0.0 - 1.0)
# Calibrated for user tabletop lane: Left line on dashed divider (0.30), Right line on road edge (0.58, excludes breadboard)
DEFAULT_CORRIDOR_X_MIN = 0.30
DEFAULT_CORRIDOR_X_MAX = 0.58

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
