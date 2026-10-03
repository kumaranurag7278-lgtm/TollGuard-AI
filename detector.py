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
        "vehicle": ["car", "bus", "truck", "motorcycle", "mouse", "suitcase"],
        "people": ["person"]
    }
    
    # Tabletop miniature proxy mapping (small toy cars seen from above can resemble these COCO shapes)
    TABLETOP_VEHICLE_REMAP = {
        "mouse": "car",
        "suitcase": "truck"
    }
    
    ONNX_URL = "https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5n.onnx"

    def __init__(self, mode="vehicle", conf_threshold=0.25, nms_threshold=0.45):
        self.mode = mode
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.model_path = os.path.join(config.MODELS_DIR, "yolov5n.onnx")
        self.net = None
        self._initialize_model()

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
        Looks for:
          1. Predominantly light / white vehicle body.
          2. Red Cross '+' emblem, red emergency stripe or beacon.
        Normal white passenger cars have virtually 0% red (or tiny taillights) and stay classified as 'car'.
        """
        if crop is None or crop.size == 0:
            return False
        ch, cw = crop.shape[:2]
        if ch < 15 or cw < 15:
            return False

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        
        # 1. White / light body ratio
        white_mask = (hsv[:, :, 1] < 75) & (hsv[:, :, 2] > 110)
        white_ratio = np.sum(white_mask) / (ch * cw)

        # 2. Red emergency markings / cross (Hue 0-12 or 165-180)
        mask_r1 = cv2.inRange(hsv, np.array([0, 80, 80]), np.array([12, 255, 255]))
        mask_r2 = cv2.inRange(hsv, np.array([165, 80, 80]), np.array([180, 255, 255]))
        red_mask = mask_r1 | mask_r2
        red_ratio = np.sum(red_mask > 0) / (ch * cw)

        # White body with distinct red insignia (between 1.2% and 35% red surface area)
        if white_ratio > 0.20 and (0.012 <= red_ratio <= 0.35):
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                _, _, rw, rh = cv2.boundingRect(cnt)
                aspect = float(rw) / max(1, rh)
                area = cv2.contourArea(cnt)
                # Red cross '+' or emergency insignia has balanced aspect ratio
                if area > (ch * cw * 0.006) and (0.40 <= aspect <= 2.5):
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

        return results
