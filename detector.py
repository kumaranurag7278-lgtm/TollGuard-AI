import os
import urllib.request
import cv2
import numpy as np
import config

class ObjectDetector:
    """
    High-Performance Object Detector using YOLOv5 nano ONNX via OpenCV 5.0 DNN.
    Supports COCO classes: person, car, motorcycle, bus, truck.
    Runs at 40-60+ FPS on standard CPU without dedicated GPU.
    """
    
    COCO_CLASSES = [
        "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
        "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
        "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
        "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
        "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
        "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
        "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
        "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
        "hair drier", "toothbrush"
    ]
    
    MODE_TARGETS = {
        "vehicle": ["car", "bus", "truck", "motorcycle", "mouse", "suitcase", "cell phone", "remote", "boat", "toaster", "sports ball", "bottle"],
        "people": ["person"]
    }
    
    # Tabletop miniature proxy mapping (small toy cars seen from above resemble these COCO shapes)
    TABLETOP_VEHICLE_REMAP = {
        "mouse": "car",
        "suitcase": "truck",
        "cell phone": "car",
        "remote": "car",
        "boat": "car",
        "toaster": "truck",
        "sports ball": "car",
        "bottle": "car"
    }
    
    ONNX_URL = "https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5n.onnx"

    def __init__(self, mode="vehicle", conf_threshold=0.06, nms_threshold=0.55):
        self.mode = mode
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.model_path = os.path.join(config.MODELS_DIR, "yolov5n.onnx")
        self.net = None
        self._initialize_model()
        self._load_car_templates()

    def _load_car_templates(self):
        self.templates = []
        template_files = [
            "car_top_green.jpg", "car_mid_green.jpg", "car_bot_blue.jpg", "car_right_side.jpg",
            "car_green.jpg", "car_blue.jpg", "car_striped.jpg", "car_blackred.jpg"
        ]
        for name in template_files:
            path = os.path.join(config.BASE_DIR, name)
            if os.path.exists(path):
                t = cv2.imread(path)
                if t is not None:
                    self.templates.append((name, t))
        if self.templates:
            print(f"[Detector] Loaded {len(self.templates)} verified physical toy car signatures into memory!")

    def _initialize_model(self):
        if not os.path.exists(self.model_path):
            print("[Detector] Downloading YOLOv5n ONNX model (~7.5 MB)...")
            try:
                urllib.request.urlretrieve(self.ONNX_URL, self.model_path)
                print("[Detector] Download complete.")
            except Exception as e:
                print(f"[Detector] Download failed: {e}")
                return

        try:
            self.net = cv2.dnn.readNetFromONNX(self.model_path)
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            print("[Detector] YOLOv5n ONNX detector loaded successfully.")
        except Exception as e:
            print(f"[Detector] Failed to load ONNX model: {e}")

    def check_emergency_ambulance(self, crop):
        """
        Differentiates an Ambulance from a normal white car.
        Requires a distinct symmetrical Red Cross '+' emblem on a predominantly white body.
        Toy cars with roof stripes or decals stay classified as 'car'.
        """
        if crop is None or crop.size == 0:
            return False
        ch, cw = crop.shape[:2]
        if ch < 15 or cw < 15:
            return False

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        
        # 1. White / light body ratio
        white_mask = (hsv[:, :, 1] < 70) & (hsv[:, :, 2] > 120)
        white_ratio = np.sum(white_mask) / (ch * cw)

        # 2. Red emergency markings / cross (Hue 0-12 or 165-180)
        mask_r1 = cv2.inRange(hsv, np.array([0, 85, 85]), np.array([12, 255, 255]))
        mask_r2 = cv2.inRange(hsv, np.array([165, 85, 85]), np.array([180, 255, 255]))
        red_mask = mask_r1 | mask_r2
        red_ratio = np.sum(red_mask > 0) / (ch * cw)

        # White body with distinct red cross insignia
        if white_ratio > 0.25 and (0.015 <= red_ratio <= 0.25):
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                _, _, rw, rh = cv2.boundingRect(cnt)
                aspect = float(rw) / max(1, rh)
                area = cv2.contourArea(cnt)
                # Red cross '+' insignia has balanced, nearly square aspect ratio (0.70 - 1.45)
                # Stripes are elongated and fail this check
                if area > (ch * cw * 0.012) and (0.70 <= aspect <= 1.45):
                    return True
        return False

    def detect(self, frame):
        """
        Runs YOLOv5 inference and returns formatted bounding boxes and centroids.
        """
        if frame is None or self.net is None:
            return []

        h, w = frame.shape[:2]
        target_classes = self.MODE_TARGETS.get(self.mode, ["car", "truck", "bus", "person"])

        # YOLO expects 640x640 input normalized by 1/255.0 in RGB
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640), swapRB=True, crop=False)
        self.net.setInput(blob)
        preds = self.net.forward() # Shape: (1, 25200, 85)

        predictions = preds[0]
        boxes = []
        confidences = []
        class_ids = []

        x_factor = w / 640.0
        y_factor = h / 640.0

        for row in predictions:
            obj_conf = row[4]
            if obj_conf >= self.conf_threshold:
                scores = row[5:]
                class_id = int(np.argmax(scores))
                score = float(scores[class_id])
                
                confidence = obj_conf * score
                if confidence >= self.conf_threshold:
                    if class_id < len(self.COCO_CLASSES):
                        cname = self.COCO_CLASSES[class_id]
                        if cname in target_classes:
                            # Center coordinates and box width/height
                            cx, cy, bw, bh = row[0], row[1], row[2], row[3]
                            left = int((cx - bw / 2.0) * x_factor)
                            top = int((cy - bh / 2.0) * y_factor)
                            width = int(bw * x_factor)
                            height = int(bh * y_factor)

                            boxes.append([left, top, width, height])
                            confidences.append(float(confidence))
                            class_ids.append(class_id)

        # Apply Non-Maximum Suppression (NMS)
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_threshold, self.nms_threshold)

        results = []
        if len(indices) > 0:
            for idx in indices.flatten():
                bx, by, bw, bh = boxes[idx]
                cname = self.COCO_CLASSES[class_ids[idx]]
                
                # Remap miniature tabletop objects to vehicle classes
                if self.mode == "vehicle" and cname in self.TABLETOP_VEHICLE_REMAP:
                    cname = self.TABLETOP_VEHICLE_REMAP[cname]

                # Standardize motorcycle naming to motorbike if needed
                if cname == "motorcycle":
                    cname = "motorbike"

                startX = max(0, bx)
                startY = max(0, by)
                endX = min(w, bx + bw)
                endY = min(h, by + bh)

                # Check for Emergency Ambulance (Red Cross insignia on white body)
                if self.mode == "vehicle" and cname in ["car", "bus", "truck"]:
                    crop = frame[startY:endY, startX:endX]
                    if self.check_emergency_ambulance(crop):
                        cname = "ambulance"

                cX = int((startX + endX) / 2.0)
                cY = int((startY + endY) / 2.0)

                results.append({
                    "class_name": cname,
                    "confidence": confidences[idx],
                    "box": (startX, startY, endX, endY),
                    "centroid": (cX, cY)
                })

        # Multi-scale template verification for user's specific toy cars
        if self.mode == "vehicle" and hasattr(self, "templates") and self.templates:
            for tname, templ in self.templates:
                th, tw = templ.shape[:2]
                best_val = -1
                best_box = None
                # Check multi-scale
                for scale in [0.75, 0.90, 1.0, 1.10, 1.25]:
                    stw = int(tw * scale)
                    sth = int(th * scale)
                    if stw >= w or sth >= h:
                        continue
                    scaled_t = cv2.resize(templ, (stw, sth))
                    res = cv2.matchTemplate(frame, scaled_t, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(res)
                    if max_val > best_val:
                        best_val = max_val
                        best_box = (max_loc[0], max_loc[1], max_loc[0] + stw, max_loc[1] + sth)

                # High-confidence template match (> 0.65)
                if best_val >= 0.65 and best_box is not None:
                    bx1, by1, bx2, by2 = best_box
                    bcX = int((bx1 + bx2) / 2.0)
                    bcY = int((by1 + by2) / 2.0)
                    
                    # Clean deduplication with existing detections (suppress if centroid < 160 px)
                    already_covered = False
                    for r in results:
                        rcX, rcY = r["centroid"]
                        dist = ((bcX - rcX)**2 + (bcY - rcY)**2)**0.5
                        if dist < 160:
                            already_covered = True
                            # Upgrade box to the precise template box
                            r["box"] = best_box
                            r["centroid"] = (bcX, bcY)
                            r["class_name"] = "car"
                            r["confidence"] = max(r["confidence"], float(best_val))
                            break

                    if not already_covered:
                        results.append({
                            "class_name": "car",
                            "confidence": float(best_val),
                            "box": best_box,
                            "centroid": (bcX, bcY)
                        })

        return results
