import os
import sys
import time
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import cv2
import numpy as np

import config
from detector import ObjectDetector
from tracker import AdaptiveCentroidTracker
from corridor import DynamicCorridorEngine
import plate_reader

# Global buffers for streaming & hardware
output_frame_lock = threading.Lock()
latest_jpeg_bytes = None

latest_esp32_data = {
    "connected": False,
    "distance_cm": 400.0,
    "rolling_cm": 400.0,
    "tinyml_state": "SHORT_WAIT",
    "last_seen": 0
}

# ==============================================================================
# HIGH-SPEED MJPEG STREAMING SERVER (FULL 30 FPS IN BROWSER)
# ==============================================================================
class MJPEGStreamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy HTTP request terminal logs
        return

    def do_GET(self):
        global latest_jpeg_bytes
        if self.path == "/video_feed":
            self.send_response(200)
            self.send_header("Age", "0")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
            self.end_headers()
            try:
                while True:
                    with output_frame_lock:
                        if latest_jpeg_bytes is None:
                            time.sleep(0.01)
                            continue
                        frame = latest_jpeg_bytes

                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
                    time.sleep(0.033)  # ~30 FPS
            except Exception:
                pass
        else:
            self.send_response(404)
            self.end_headers()


def start_mjpeg_server(port=5001):
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), MJPEGStreamHandler)
        print(f"[MJPEG Server] High-speed 30 FPS stream active on http://localhost:{port}/video_feed")
        server.serve_forever()
    except Exception as e:
        print(f"[MJPEG Server] Error starting stream server: {e}")


# ==============================================================================
# ESP32 HARDWARE SERIAL READER
# ==============================================================================
def esp32_serial_reader_thread(port="COM9", baudrate=115200):
    global latest_esp32_data
    import serial
    print(f"[ESP32 Reader] Connecting to physical hardware on {port}...")
    
    while True:
        try:
            ser = serial.Serial(port, baudrate, timeout=2)
            print(f"[ESP32 Reader] Successfully connected to {port}.")
            latest_esp32_data["connected"] = True
            
            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if line and "[Sensor]" in line:
                    try:
                        parts = line.split("|")
                        dist_part = parts[0].split("Distance:")[1].split("cm")[0].strip()
                        roll_part = parts[1].split("Rolling:")[1].split("cm")[0].strip()
                        ai_part = parts[2].split(">>>")[1].split("<<<")[0].strip()
                        
                        latest_esp32_data["distance_cm"] = float(dist_part)
                        latest_esp32_data["rolling_cm"] = float(roll_part)
                        latest_esp32_data["tinyml_state"] = ai_part
                        latest_esp32_data["last_seen"] = time.time()
                    except Exception:
                        pass
        except Exception:
            latest_esp32_data["connected"] = False
            time.sleep(2.0)


def calculate_weighted_wait_time(active_objects, mode="people"):
    total_seconds = 0
    breakdown = {}
    for obj in active_objects.values():
        cname = obj.class_name
        breakdown[cname] = breakdown.get(cname, 0) + 1
        service_dur = config.SERVICE_TIMES_SEC.get(cname, 30)
        total_seconds += service_dur
    return total_seconds, breakdown


def draw_visual_overlays(frame, active_objects, corridor_status, wait_seconds, breakdown, mode="people"):
    h, w = frame.shape[:2]
    annotated = frame.copy()

    # 1. Service / Barrier Zone
    barrier_y = corridor_status.get("barrier_zone_y", int(h * 0.2))
    cv2.line(annotated, (0, barrier_y), (w, barrier_y), (0, 255, 255), 2)
    cv2.putText(annotated, "SERVICE / BARRIER ZONE", (15, barrier_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # 2. Dynamic Back-Edge Line
    back_edge_y = corridor_status.get("dynamic_back_edge_y")
    if back_edge_y is not None:
        cv2.line(annotated, (0, back_edge_y), (w, back_edge_y), (0, 165, 255), 2)
        cv2.putText(annotated, f"DYNAMIC BACK EDGE (Entry: Y={back_edge_y})", 
                    (15, min(h - 10, back_edge_y + 18)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)

    # 3. Lateral Corridor Guidelines
    x_min = int(w * config.DEFAULT_CORRIDOR_X_MIN)
    x_max = int(w * config.DEFAULT_CORRIDOR_X_MAX)
    cv2.line(annotated, (x_min, 0), (x_min, h), (255, 150, 0), 1)
    cv2.line(annotated, (x_max, 0), (x_max, h), (255, 150, 0), 1)

    # 4. Tracked Objects
    for obj in active_objects.values():
        startX, startY, endX, endY = obj.box
        cX, cY = obj.centroid

        plate_str = f" [{obj.license_plate}]" if getattr(obj, "license_plate", None) else ""
        if getattr(obj, "class_name", "") == "ambulance":
            box_color = (0, 255, 100)  # Bright emerald green for emergency
            label = f"[!] AMBULANCE #{obj.token_number}{plate_str}"
        elif obj.is_violator:
            box_color = (0, 0, 255)
            label = f"[!] CUTTER #{obj.token_number}{plate_str} ({obj.class_name.upper()})"
        else:
            box_color = (0, 255, 0)
            label = f"#{obj.token_number} {obj.class_name}{plate_str}"

        cv2.rectangle(annotated, (startX, startY), (endX, endY), box_color, 2)
        cv2.circle(annotated, (cX, cY), 4, box_color, -1)

        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        lbl_y = max(startY - 5, label_size[1] + 5)
        cv2.rectangle(annotated, (startX, lbl_y - label_size[1] - 4), 
                      (startX + label_size[0] + 6, lbl_y + 2), box_color, -1)
        cv2.putText(annotated, label, (startX + 3, lbl_y - 2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

    # 5. Top HUD Panel
    hud_h = 60
    overlay = annotated.copy()
    cv2.rectangle(overlay, (0, 0), (w, hud_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, annotated, 0.25, 0, annotated)

    wait_min = wait_seconds // 60
    wait_sec = wait_seconds % 60
    status_text = "ENFORCING" if corridor_status.get("corridor_active") else "STANDBY (<3 in queue)"
    status_color = (0, 255, 0) if corridor_status.get("corridor_active") else (0, 200, 255)
    breakdown_str = ", ".join([f"{k}: {v}" for k, v in breakdown.items()]) if breakdown else "Queue Empty"
    
    cv2.putText(annotated, f"QUEUE MONITOR [{mode.upper()}] | Status: {status_text}", 
                (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.52, status_color, 2)
    cv2.putText(annotated, f"Count: {len(active_objects)} ({breakdown_str}) | Est. Wait: {wait_min}m {wait_sec}s", 
                (12, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (240, 240, 240), 1)

    return annotated


def run_pipeline(source=0, mode="people", show_window=False):
    global latest_jpeg_bytes
    print(f"[QueueCamera] Starting in '{mode}' mode (Camera: {source})...")
    
    # Start MJPEG streaming server in background
    stream_thread = threading.Thread(target=start_mjpeg_server, args=(5001,), daemon=True)
    stream_thread.start()

    # Launch ESP32 serial reader thread
    serial_thread = threading.Thread(target=esp32_serial_reader_thread, args=("COM9", 115200), daemon=True)
    serial_thread.start()

    detector = ObjectDetector(mode=mode)
    tracker = AdaptiveCentroidTracker()
    corridor_engine = DynamicCorridorEngine()

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[QueueCamera] Unable to open camera '{source}', using fallback frame.")
        cap = None

    try:
        while True:
            start_t = time.time()

            if cap is not None and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
            else:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                frame[:] = (35, 35, 35)
                cv2.putText(frame, "Awaiting Camera Feed...", (180, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

            # 1. Detection
            detections = detector.detect(frame)

            # 2. Tracking
            active_objects = tracker.update(detections)

            # 3. Dynamic Corridor Evaluation
            corridor_status = corridor_engine.evaluate_queue(active_objects, frame)

            # 4. Wait Time
            wait_seconds, breakdown = calculate_weighted_wait_time(active_objects, mode=mode)

            # 5. Overlays
            annotated_frame = draw_visual_overlays(
                frame, active_objects, corridor_status, wait_seconds, breakdown, mode=mode
            )

            # 6. Encode Frame to JPEG for MJPEG browser stream (30 FPS)
            ret, jpeg = cv2.imencode(".jpg", annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                with output_frame_lock:
                    latest_jpeg_bytes = jpeg.tobytes()

            # 7. Nearest entity at barrier
            front_vehicle = None
            if active_objects:
                nearest = min(active_objects.values(), key=lambda o: o.centroid[1])
                if not getattr(nearest, "license_plate", None):
                    plate_rec = plate_reader.plate_engine.get_or_register_plate(nearest.token_number, nearest.class_name)
                    nearest.license_plate = plate_rec["plate_number"]
                    nearest.plate_snapshot = plate_rec["plate_snapshot"]
                    nearest.plate_type = plate_rec["plate_type"]

                is_emergency = getattr(nearest, "class_name", "") == "ambulance"
                front_vehicle = {
                    "token": nearest.token_number,
                    "class": nearest.class_name,
                    "license_plate": getattr(nearest, "license_plate", "N/A"),
                    "plate_snapshot": getattr(nearest, "plate_snapshot", None),
                    "plate_type": getattr(nearest, "plate_type", "PRIVATE (WHITE)"),
                    "is_violator": nearest.is_violator and not is_emergency,
                    "violation_reason": nearest.violation_reason,
                    "penalty": config.VIOLATION_PENALTY if (nearest.is_violator and not is_emergency) else 0,
                    "base_fare": 0 if is_emergency else config.BASE_TOLL_FARE,
                    "is_emergency": is_emergency,
                    "fastag_category": getattr(nearest, "fastag_category", "CAR"),
                    "fastag_mismatch": getattr(nearest, "fastag_mismatch", False),
                    "fastag_mismatch_reason": getattr(nearest, "fastag_mismatch_reason", None)
                }

            # 8. Write complete state
            live_state = {
                "timestamp": time.time(),
                "mode": mode,
                "active_count": len(active_objects),
                "breakdown": breakdown,
                "wait_seconds": wait_seconds,
                "corridor_active": corridor_status["corridor_active"],
                "back_edge_y": corridor_status["dynamic_back_edge_y"],
                "front_entity": front_vehicle,
                "total_violations_today": len(corridor_engine.violations_history),
                "esp32_connected": latest_esp32_data["connected"],
                "esp32_distance": latest_esp32_data["distance_cm"],
                "esp32_tinyml": latest_esp32_data["tinyml_state"]
            }

            try:
                temp_file = config.LIVE_STATE_FILE + ".tmp"
                with open(temp_file, "w") as f:
                    json.dump(live_state, f)
                if os.path.exists(config.LIVE_STATE_FILE):
                    os.replace(temp_file, config.LIVE_STATE_FILE)
                else:
                    os.rename(temp_file, config.LIVE_STATE_FILE)
            except Exception:
                pass

            if show_window:
                cv2.imshow("AI Queue & Toll Camera", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            time.sleep(0.033)

    except KeyboardInterrupt:
        pass
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    mode_arg = sys.argv[1] if len(sys.argv) > 1 else "people"
    src_arg = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 0
    show_win = "--show-window" in sys.argv
    run_pipeline(source=src_arg, mode=mode_arg, show_window=show_win)
