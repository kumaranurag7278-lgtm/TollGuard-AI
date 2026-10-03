import time
from collections import OrderedDict
import numpy as np
import config

class TrackedObject:
    """Represents an active entity (person or vehicle) within the queue or lane."""
    def __init__(self, object_id, token_number, centroid, box, class_name):
        self.object_id = object_id
        self.token_number = token_number  # Sequential virtual queue token
        self.centroid = centroid
        self.box = box
        self.class_name = class_name
        self.first_seen_centroid = centroid
        self.first_seen_time = time.time()
        self.last_seen_time = time.time()
        self.missed_frames = 0
        self.trajectory = [centroid]
        
        # Violation & ANPR License Plate state
        self.is_violator = False
        self.violation_reason = None
        self.evidence_snapshot = None
        self.license_plate = None
        self.plate_snapshot = None
        self.plate_type = None
        self.has_reached_barrier = False

        # Advanced Intelligent Features: Emergency Preemption & FASTag Verification
        self.is_emergency = (class_name == "ambulance")
        self.fastag_category = "CAR" if class_name == "car" else ("TRUCK" if class_name == "truck" else ("BUS" if class_name == "bus" else "EMERGENCY"))
        self.fastag_mismatch = False
        self.fastag_mismatch_reason = None

    def update(self, centroid, box):
        self.centroid = centroid
        self.box = box
        self.missed_frames = 0
        self.last_seen_time = time.time()
        self.trajectory.append(centroid)
        if len(self.trajectory) > 50:
            self.trajectory.pop(0)


class AdaptiveCentroidTracker:
    """
    Centroid Tracker with adaptive missed-frame distance compensation:
      allowed_distance = base_distance + (missed_frames * per_frame_motion_allowance)
    
    Prevents ID duplication caused by detector flicker when objects continue moving
    during brief missed detections.
    """
    def __init__(self, 
                 base_distance=config.TRACKER_BASE_DISTANCE, 
                 motion_allowance=config.TRACKER_PER_FRAME_ALLOWANCE, 
                 max_missed=config.MAX_MISSED_FRAMES):
        self.next_object_id = 1
        self.objects = OrderedDict()  # {object_id: TrackedObject}
        self.base_distance = base_distance
        self.motion_allowance = motion_allowance
        self.max_missed = max_missed

    def register(self, centroid, box, class_name):
        obj_id = self.next_object_id
        token_num = obj_id  # Virtual Token #N
        self.objects[obj_id] = TrackedObject(
            object_id=obj_id,
            token_number=token_num,
            centroid=centroid,
            box=box,
            class_name=class_name
        )
        self.next_object_id += 1
        return self.objects[obj_id]

    def deregister(self, object_id):
        if object_id in self.objects:
            del self.objects[object_id]

    def update(self, detected_items):
        """
        Updates tracker state given detection results:
        detected_items: list of dicts with 'centroid', 'box', 'class_name'
        """
        # If no detections are present in the current frame
        if len(detected_items) == 0:
            deregister_ids = []
            for obj_id, obj in self.objects.items():
                obj.missed_frames += 1
                if obj.missed_frames > self.max_missed:
                    deregister_ids.append(obj_id)
            for obj_id in deregister_ids:
                self.deregister(obj_id)
            return self.objects

        # If currently tracking nothing, register all incoming detections
        if len(self.objects) == 0:
            for item in detected_items:
                self.register(item["centroid"], item["box"], item["class_name"])
            return self.objects

        # Extract existing IDs and centroids
        object_ids = list(self.objects.keys())
        existing_centroids = np.array([self.objects[oid].centroid for oid in object_ids])
        input_centroids = np.array([item["centroid"] for item in detected_items])

        # Compute pairwise Euclidean distance matrix
        # Shape: (num_existing_objects, num_detections)
        dist_matrix = np.linalg.norm(
            existing_centroids[:, np.newaxis] - input_centroids[np.newaxis, :], 
            axis=2
        )

        # Sort matrix rows and columns for greedy minimum-distance association
        rows = dist_matrix.min(axis=1).argsort()
        cols = dist_matrix.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue

            obj_id = object_ids[row]
            obj = self.objects[obj_id]
            dist = dist_matrix[row, col]

            # Adaptive dynamic distance threshold calculation
            # Scales proportionally with duration of brief detector dropout
            effective_threshold = self.base_distance + (obj.missed_frames * self.motion_allowance)

            if dist <= effective_threshold:
                # Valid match
                obj.update(detected_items[col]["centroid"], detected_items[col]["box"])
                used_rows.add(row)
                used_cols.add(col)

        # Handle unmatched existing objects (increment missed count)
        unused_rows = set(range(len(object_ids))) - used_rows
        for row in unused_rows:
            obj_id = object_ids[row]
            self.objects[obj_id].missed_frames += 1
            if self.objects[obj_id].missed_frames > self.max_missed:
                self.deregister(obj_id)

        # Handle unmatched detections (new objects entering the scene)
        unused_cols = set(range(len(detected_items))) - used_cols
        newly_registered = []
        for col in unused_cols:
            new_obj = self.register(
                detected_items[col]["centroid"], 
                detected_items[col]["box"], 
                detected_items[col]["class_name"]
            )
            newly_registered.append(new_obj)

        return self.objects
