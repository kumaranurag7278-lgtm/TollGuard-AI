import os
import sys
import time
import json
import random
import cv2
import numpy as np

import config
from corridor import DynamicCorridorEngine
from tracker import TrackedObject
import plate_reader

def run_simulation(duration_sec=300):
    """
    Simulates a live toll plaza lane with vehicles joining legitimately
    and an intentional lane-cutter to demonstrate live violation detection and dashboard reaction.
    """
    print("=" * 60)
    print("STARTING TOLL PLAZA & CORRIDOR SIMULATION")
    print("Open the dashboard in another terminal using:")
    print("    streamlit run dashboard.py")
    print("=" * 60)

    corridor_engine = DynamicCorridorEngine()
    width, height = 640, 480
    barrier_y = int(height * config.SERVICE_BARRIER_Y_RATIO)

    # Initialize simulated queue
    active_objects = {}
    next_id = 1
    
    # Pre-populate 4 legitimate vehicles in line
    classes = ["car", "truck", "car", "bus"]
    y_positions = [barrier_y + 40, barrier_y + 110, barrier_y + 190, barrier_y + 280]

    for cname, y in zip(classes, y_positions):
        x = 320 + random.randint(-15, 15)
        w_box = 70 if cname == "car" else (90 if cname == "bus" else 100)
        h_box = 50 if cname == "car" else 70
        box = (x - w_box//2, y - h_box//2, x + w_box//2, y + h_box//2)
        obj = TrackedObject(next_id, next_id, (x, y), box, cname)
        active_objects[next_id] = obj
        next_id += 1

    step = 0
    start_time = time.time()

    while time.time() - start_time < duration_sec:
        step += 1
        
        # Create base canvas representing highway toll approach
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (35, 35, 35) # Asphalt road

        # Draw road lane markings
        cv2.line(frame, (160, 0), (160, height), (255, 255, 255), 2)
        cv2.line(frame, (480, 0), (480, height), (255, 255, 255), 2)
        # Center dashed yellow line
        for dy in range(0, height, 40):
            cv2.line(frame, (320, dy), (320, dy + 20), (0, 220, 255), 2)

        # Advance vehicles forward slowly toward barrier
        for obj in list(active_objects.values()):
            cX, cY = obj.centroid
            # Move towards barrier
            new_y = cY - 2
            
            # If vehicle reaches barrier, hold for a few seconds then clear
            if new_y <= barrier_y + 15:
                if step % 25 == 0:
                    # Vehicle cleared through barrier!
                    del active_objects[obj.object_id]
                    continue
                new_y = barrier_y + 15

            w_box = obj.box[2] - obj.box[0]
            h_box = obj.box[3] - obj.box[1]
            obj.update((cX, new_y), (cX - w_box//2, new_y - h_box//2, cX + w_box//2, new_y + h_box//2))

        # At step 15, simulate a deliberate LANE-CUTTER vehicle cutting in from the side at Y=200!
        if step == 15:
            print("\n[SIMULATION] >>> INJECTING LATERAL LANE-CUTTER VEHICLE AT Y=200! <<<")
            cutter_x = 320
            cutter_y = barrier_y + 70 # In between cars ahead!
            cutter_box = (cutter_x - 35, cutter_y - 25, cutter_x + 35, cutter_y + 25)
            cutter_obj = TrackedObject(next_id, next_id, (cutter_x, cutter_y), cutter_box, "car")
            active_objects[next_id] = cutter_obj
            next_id += 1

        # At step 40, add a legitimate vehicle at the very back
        if step % 45 == 0 and len(active_objects) < 6:
            back_y = max([o.centroid[1] for o in active_objects.values()]) + 80 if active_objects else height - 60
            if back_y < height - 30:
                cname = random.choice(["car", "truck", "car"])
                x = 320 + random.randint(-10, 10)
                box = (x - 35, back_y - 25, x + 35, back_y + 25)
                new_obj = TrackedObject(next_id, next_id, (x, back_y), box, cname)
                active_objects[next_id] = new_obj
                next_id += 1

        # At step 30, simulate incoming EMERGENCY AMBULANCE with Green Corridor Preemption!
        if step == 30:
            print("\n[SIMULATION] >>> [!] INCOMING EMERGENCY AMBULANCE! (GREEN WAVE CORRIDOR PREEMPTION) <<<")
            amb_x = 320
            amb_y = height - 50
            amb_box = (amb_x - 35, amb_y - 25, amb_x + 35, amb_y + 25)
            amb_obj = TrackedObject(next_id, next_id, (amb_x, amb_y), amb_box, "ambulance")
            amb_obj.license_plate = "PB 65 AM 1080"
            amb_obj.is_emergency = True
            active_objects[next_id] = amb_obj
            next_id += 1

        # Render simulated vehicles on canvas
        for obj in active_objects.values():
            sX, sY, eX, eY = obj.box
            if obj.class_name == "ambulance":
                color = (250, 250, 250) # Pure White Ambulance Body
            elif obj.is_violator:
                color = (0, 0, 220)
            else:
                color = (80, 200, 80) if obj.class_name == "car" else (220, 140, 40)
            cv2.rectangle(frame, (sX, sY), (eX, eY), color, -1)
            cv2.rectangle(frame, (sX, sY), (eX, eY), (255, 255, 255), 1)

            # Draw Red Cross '+' on Ambulance roof
            if obj.class_name == "ambulance":
                cenX, cenY = obj.centroid
                cv2.rectangle(frame, (cenX - 7, cenY - 2), (cenX + 7, cenY + 2), (0, 0, 230), -1)
                cv2.rectangle(frame, (cenX - 2, cenY - 7), (cenX + 2, cenY + 7), (0, 0, 230), -1)

        # Run dynamic corridor violation checks
        corridor_status = corridor_engine.evaluate_queue(active_objects, frame)

        # Calculate PCU-weighted wait time
        wait_sec = sum([config.SERVICE_TIMES_SEC.get(o.class_name, 30) for o in active_objects.values()])
        breakdown = {}
        for o in active_objects.values():
            breakdown[o.class_name] = breakdown.get(o.class_name, 0) + 1

        # Draw overlays
        annotated = frame.copy()
        # Barrier line
        cv2.line(annotated, (0, barrier_y), (width, barrier_y), (0, 255, 255), 2)
        cv2.putText(annotated, "TOLL BOOM BARRIER", (15, barrier_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        
        # Dynamic back edge
        back_y = corridor_status.get("dynamic_back_edge_y")
        if back_y:
            cv2.line(annotated, (0, back_y), (width, back_y), (0, 165, 255), 2)
            cv2.putText(annotated, f"DYNAMIC BACK EDGE (Y={back_y})", (15, min(height - 10, back_y + 16)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)

        # Draw vehicle labels
        for obj in active_objects.values():
            if not getattr(obj, "license_plate", None):
                rec = plate_reader.plate_engine.get_or_register_plate(obj.token_number, obj.class_name)
                obj.license_plate = rec["plate_number"]
                obj.plate_snapshot = rec["plate_snapshot"]
                obj.plate_type = rec["plate_type"]

            plate_tag = f" [{obj.license_plate}]" if obj.license_plate else ""
            lbl = f"CUTTER #{obj.token_number}{plate_tag}" if obj.is_violator else f"#{obj.token_number} {obj.class_name}{plate_tag}"
            color = (0, 0, 255) if obj.is_violator else (0, 255, 0)
            cv2.putText(annotated, lbl, (obj.box[0], max(15, obj.box[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1)

        # Nearest vehicle at barrier
        front_vehicle = None
        if active_objects:
            nearest = min(active_objects.values(), key=lambda o: o.centroid[1])
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
                "fastag_mismatch": getattr(nearest, "fastag_mismatch", False)
            }

        # Save live state for dashboard
        live_state = {
            "timestamp": time.time(),
            "mode": "vehicle",
            "active_count": len(active_objects),
            "breakdown": breakdown,
            "wait_seconds": wait_sec,
            "corridor_active": corridor_status["corridor_active"],
            "back_edge_y": corridor_status["dynamic_back_edge_y"],
            "front_entity": front_vehicle,
            "total_violations_today": len(corridor_engine.violations_history)
        }

        try:
            with open(config.LIVE_STATE_FILE, "w") as f:
                json.dump(live_state, f)
            cv2.imwrite(os.path.join(config.ALERTS_DIR, "live_stream.jpg"), annotated)
        except Exception:
            pass

        time.sleep(0.35)

    print("[Simulation] Completed successfully.")

if __name__ == "__main__":
    run_simulation()
