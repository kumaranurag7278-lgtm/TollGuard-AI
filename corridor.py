import os
import json
import time
from datetime import datetime
import cv2
import config
import plate_reader

class DynamicCorridorEngine:
    """
    Implements Dynamic Queue Corridor Integrity & Anti-Lane-Cutting / Anti-Skip Detection:
    1. Dynamic Back-Edge: Continuously tracks the position of the last legitimate queue member.
    2. Mid-Corridor Lateral Entry Detection: Flags any new object appearing ahead of the back edge.
    3. Out-of-Sequence Counter Arrival: Flags objects reaching the counter out of token order.
    4. Low-Occupancy Guard: Dormant when fewer than 3 objects are tracked to eliminate false alarms.
    5. Automatic Evidence Logging: Crops and saves timestamped visual proof for fine enforcement.
    """
    
    def __init__(self):
        self.violations_history = []
        self._load_violations_history()

    def _load_violations_history(self):
        if os.path.exists(config.VIOLATIONS_FILE):
            try:
                with open(config.VIOLATIONS_FILE, "r") as f:
                    self.violations_history = json.load(f)
            except Exception:
                self.violations_history = []

    def _save_violation_entry(self, entry):
        self.violations_history.append(entry)
        try:
            with open(config.VIOLATIONS_FILE, "w") as f:
                json.dump(self.violations_history, f, indent=2)
        except Exception as e:
            print(f"[Corridor] Error persisting violation log: {e}")

    def capture_evidence_snapshot(self, frame, obj, violation_type):
        """
        Extracts cropped snapshot of the violating vehicle or person with an overlaid citation banner.
        Also runs ANPR to extract/generate license plate and saves cropped HSRP evidence.
        Saves image into the alerts/ directory.
        """
        h, w = frame.shape[:2]
        startX, startY, endX, endY = obj.box
        
        # Add padding around bounding box for visual context
        pad_x = int((endX - startX) * 0.3)
        pad_y = int((endY - startY) * 0.3)
        crop_x1 = max(0, startX - pad_x)
        crop_y1 = max(0, startY - pad_y)
        crop_x2 = min(w, endX + pad_x)
        crop_y2 = min(h, endY + pad_y)

        evidence_frame = frame[crop_y1:crop_y2, crop_x1:crop_x2].copy()
        if evidence_frame.size == 0:
            evidence_frame = frame.copy()

        # Run ANPR plate reader
        plate_record = plate_reader.plate_engine.get_or_register_plate(
            obj.token_number, obj.class_name, evidence_frame
        )
        obj.license_plate = plate_record["plate_number"]
        obj.plate_snapshot = plate_record["plate_snapshot"]
        obj.plate_type = plate_record["plate_type"]

        # Overlay violation banner onto the evidence snapshot
        banner_h = 52
        eh, ew = evidence_frame.shape[:2]
        cv2.rectangle(evidence_frame, (0, 0), (ew, banner_h), (0, 0, 180), -1)
        
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text_line1 = f"VIOLATION: {violation_type} | ID #{obj.token_number} ({obj.class_name.upper()})"
        text_line2 = f"PLATE: {obj.license_plate} | FINE: INR {config.VIOLATION_PENALTY} | {timestamp_str}"
        
        cv2.putText(evidence_frame, text_line1, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1)
        cv2.putText(evidence_frame, text_line2, (10, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 255, 255), 1)

        filename = f"violation_id_{obj.token_number}_{int(time.time())}.jpg"
        filepath = os.path.join(config.ALERTS_DIR, filename)
        cv2.imwrite(filepath, evidence_frame)
        return filename

    def evaluate_queue(self, active_objects, current_frame):
        """
        Evaluates active tracked entities against corridor boundaries and sequence tokens.
        
        Returns:
            dict: {
                "dynamic_back_edge_y": int or None,
                "corridor_active": bool,
                "barrier_zone_y": int,
                "violations_flagged_this_frame": list
            }
        """
        if current_frame is None or len(active_objects) == 0:
            return {
                "dynamic_back_edge_y": None,
                "corridor_active": False,
                "barrier_zone_y": 0,
                "violations_flagged_this_frame": []
            }

        h, w = current_frame.shape[:2]
        barrier_y = int(h * config.SERVICE_BARRIER_Y_RATIO)
        
        # Rule 1: Low-Occupancy Guard
        # If queue occupancy < 3, geometry is ambiguous; deactivate violation triggers
        if len(active_objects) < config.MIN_OBJECTS_FOR_ENFORCEMENT:
            return {
                "dynamic_back_edge_y": None,
                "corridor_active": False,
                "barrier_zone_y": barrier_y,
                "violations_flagged_this_frame": []
            }

        # Identify dynamic back edge:
        # Standard queue model assumes service barrier is at top (low Y), entrance is at bottom (high Y).
        # Legitimate last person has maximum Y coordinate among existing queue members.
        all_y_coords = [obj.centroid[1] for obj in active_objects.values()]
        # Back edge is the deepest position in the line
        dynamic_back_edge_y = max(all_y_coords)

        violations_this_frame = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sort objects by token number (arrival order)
        sorted_by_token = sorted(active_objects.values(), key=lambda o: o.token_number)

        for obj in sorted_by_token:
            # Emergency Vehicle Preemption: Ambulances have statutory right of way
            if getattr(obj, "class_name", "") == "ambulance":
                obj.is_violator = False
                obj.is_emergency = True
                continue

            # Check 1: Mid-Corridor Lateral Entry / Line Jumping
            # Flag if the object first appeared well ahead of the dynamic back edge
            # (i.e. first_seen Y was significantly closer to the counter than the back of the queue)
            if not obj.is_violator and len(obj.trajectory) >= 3:
                # If its first appearance Y coordinate was closer to barrier than the back-edge tolerance
                # AND there were at least MIN_OBJECTS behind it when it appeared
                y_first = obj.first_seen_centroid[1]
                
                # Check how many objects were already present and deeper in line
                deeper_objects = [
                    other for other in active_objects.values() 
                    if other.token_number < obj.token_number and other.centroid[1] > (y_first + config.BACK_EDGE_TOLERANCE_PX)
                ]

                if len(deeper_objects) >= 2:
                    # Clear cut: At least 2 legitimate vehicles/people were behind this insertion point
                    obj.is_violator = True
                    obj.violation_reason = "Mid-Corridor Lane Cutting"
                    snapshot_file = self.capture_evidence_snapshot(current_frame, obj, obj.violation_reason)
                    obj.evidence_snapshot = snapshot_file

                    violation_record = {
                        "id": obj.token_number,
                        "class_name": obj.class_name,
                        "license_plate": getattr(obj, "license_plate", "N/A"),
                        "plate_snapshot": getattr(obj, "plate_snapshot", None),
                        "plate_type": getattr(obj, "plate_type", "PRIVATE (WHITE)"),
                        "violation_type": obj.violation_reason,
                        "timestamp": now_str,
                        "penalty_inr": config.VIOLATION_PENALTY,
                        "status": "UNPAID",
                        "snapshot": snapshot_file
                    }
                    self._save_violation_entry(violation_record)
                    violations_this_frame.append(violation_record)

            # Check 2: Out-of-Sequence Counter Arrival
            # Flag if an entity arrives in the barrier service zone while an older token is still waiting behind
            cX, cY = obj.centroid
            if cY <= barrier_y and not obj.has_reached_barrier:
                obj.has_reached_barrier = True
                
                # Check if any earlier token is still unserved and positioned behind in the queue
                unserved_precedents = [
                    other for other in active_objects.values()
                    if other.token_number < obj.token_number 
                    and not other.has_reached_barrier 
                    and other.centroid[1] > barrier_y
                ]

                if len(unserved_precedents) > 0 and not obj.is_violator:
                    obj.is_violator = True
                    obj.violation_reason = f"Out-of-Order Queue Bypass (Bypassed Token #{unserved_precedents[0].token_number})"
                    snapshot_file = self.capture_evidence_snapshot(current_frame, obj, "Sequence Bypass")
                    obj.evidence_snapshot = snapshot_file

                    violation_record = {
                        "id": obj.token_number,
                        "class_name": obj.class_name,
                        "license_plate": getattr(obj, "license_plate", "N/A"),
                        "plate_snapshot": getattr(obj, "plate_snapshot", None),
                        "plate_type": getattr(obj, "plate_type", "PRIVATE (WHITE)"),
                        "violation_type": obj.violation_reason,
                        "timestamp": now_str,
                        "penalty_inr": config.VIOLATION_PENALTY,
                        "status": "UNPAID",
                        "snapshot": snapshot_file
                    }
                    self._save_violation_entry(violation_record)
                    violations_this_frame.append(violation_record)

        return {
            "dynamic_back_edge_y": dynamic_back_edge_y,
            "corridor_active": True,
            "barrier_zone_y": barrier_y,
            "violations_flagged_this_frame": violations_this_frame
        }
