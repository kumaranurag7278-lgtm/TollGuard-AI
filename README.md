# 🚦 TollGuard-AI: AI-Powered Smart Highway Toll Plaza & Queue Enforcement System

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.14-blue?logo=python&logoColor=white)](https://python.org)
[![ESP32](https://img.shields.io/badge/Hardware-ESP32%20DevKit%20V1-red?logo=espressif&logoColor=white)](https://espressif.com)
[![Edge AI](https://img.shields.io/badge/Edge%20AI-TinyML%20Decision%20Tree-orange?logo=arduino&logoColor=white)](https://github.com)
[![Vision](https://img.shields.io/badge/Vision%20AI-YOLOv5%20Nano%20ONNX-green?logo=opencv&logoColor=white)](https://opencv.org)
[![Framework](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **CGC University Mohali | Department of Artificial Intelligence & Data Science**  
> *Engineering Clinic Project #190: IoT Sensor Fusion, Edge AI (TinyML), Computer Vision & Automated Highway Law Enforcement*

---

## 📌 Overview

**TollGuard-AI** is a production-grade, multi-modal highway toll plaza and customer queue management system. It combines low-cost IoT physical proximity sensing (**ESP32 + HC-SR04**) with high-speed real-time Computer Vision (**YOLOv5 nano ONNX**), **Automatic Number Plate Recognition (ANPR)**, and on-chip **TinyML Edge AI** to solve real-world highway bottlenecks, prevent hazardous lane-cutting, and automate statutory traffic fine collection under the **Motor Vehicles Act 1988**.

Traditional toll plazas rely on static single-sensor distance thresholds that fail to detect behavioral infractions such as queue-cutting, lane skipping, or FASTag fraud. **TollGuard-AI** provides autonomous spatial queue monitoring, automated e-Challan generation with high-resolution photographic proof, emergency vehicle green corridor preemption, and real-time physical boom barrier lockout.

---

## 🌟 Key Features

### 1. 📹 Real-Time 30 FPS Computer Vision & Tracking
- **YOLOv5 Nano ONNX Engine:** Ultra-lightweight (7.5 MB, ~1.9M parameters) single-stage convolutional neural network executed via **OpenCV 5.0 DNN**, achieving **35–50 FPS on standard CPUs** without requiring a dedicated GPU.
- **Adaptive Centroid Tracker:** Dynamically compensates for detector dropouts via temporal motion allowance (`allowed_distance = base + (missed * allowance)`), assigning permanent sequential virtual tokens (`#1, #2, #3...`).

### 2. 🛡️ Dynamic Back-Edge Corridor Integrity (Anti-Lane-Cutting)
- **Autonomous Spatial Queue Analysis:** Continuously computes the coordinate of the legitimate tail of the line (`y_back_edge = max(all_y_coordinates)`).
- **Forced Lateral Entry Detection:** Flags vehicles that cut in laterally ahead of waiting patrons. Automatically locks the physical boom barrier and logs timestamped evidence.

### 3. 🔍 Automatic Number Plate Recognition (ANPR) & e-Challan
- **Bumper Zone Localization:** Uses morphological top-hat filtering, bilateral edge-preserving smoothing, and adaptive thresholding to extract vehicle license plates.
- **Indian HSRP Plate Engine:** Identifies/extracts authentic Indian High-Security Registration Plates (`PB 65 CD 4199`), distinguishing between **Private (White)** and **Commercial (Yellow)** formats with the official blue **`IND`** security stripe.
- **Statutory Enforcement:** Imposes an automated **₹500 fine under Section 177 of the Motor Vehicles Act 1988** and logs cryptographic case records in `violations.json`.

### 4. 🚑 Emergency Ambulance "Green Corridor" Preemption
- **Insignia-Based Ambulance Classifier:** Differentiates legitimate emergency vehicles from normal white cars using a **Dual-Layer Medical Insignia Filter** (HSV red-cross `+` contour morphology and white body ratio test).
- **Automated Green Wave:** Instantly lifts the boom barrier (`🟢 BOOM BARRIER: AUTO-LIFTED`), waives toll fare (₹0.00), and preempts traffic under **Section 194E, Motor Vehicles Act**.

### 5. 🕵️ FASTag Tag-Swap / Clone Fraud Detection
- **Visual AI vs. RFID Cross-Verification:** Compares visual vehicle class against scanned FASTag category.
- **Evasion Penalty:** Catches multi-axle freight trucks fraudulently using Class I car tags, imposing an immediate **3x evasion fine (₹1,350)** and blacklisting the cloned tag.

### 6. 📲 Direct WhatsApp Official e-Challan Dispatch
- Integrates a one-click digital police dispatch link (`https://wa.me/`) generating an official formatted traffic notice with vehicle plate, location, violation proof, and statutory citations directly to the owner's mobile without requiring QR codes.

### 7. 🧠 On-Chip Edge AI (TinyML on ESP32)
- **Zero Cloud Latency:** A quantized C++ Decision Tree (`queue_tinyml_model.h`, max depth 4, 99.5% accuracy) runs directly on the ESP32 Xtensa Dual-Core 240MHz CPU in **< 15 microseconds**.
- **Offline Autonomy:** Continues queue state classification (`SHORT_WAIT`, `MEDIUM_WAIT`, `LONG_WAIT`) even during complete internet or cloud outages.

### 8. ⏱️ Passenger Car Unit (PCU) Wait-Time Forecasting
- Clearance times are projected using civil engineering **Passenger Car Unit (PCU)** service duration weighting (Car: 15s, Motorcycle: 8s, Bus: 35s, Truck: 50s) rather than naive headcounts.

---

## 🏗️ System Architecture

```
                                  +---------------------------------------+
                                  |      Overhead Camera / Smartphone     |
                                  |    (35-degree Angled Gantry Portal)   |
                                  +-------------------+-------------------+
                                                      |
                                                      | 30 FPS Stream
                                                      v
+-------------------------------+         +-------------------------------+
|    Physical ESP32 Edge Node   |         |      Host Laptop (Python)     |
|  - HC-SR04 Ultrasonic Sensor  |         |  - OpenCV DNN (YOLOv5n ONNX)  |
|  - On-Chip TinyML Decision    |  UART   |  - Adaptive Centroid Tracker  |
|  - 3.3V Voltage Divider       | ------> |  - Dynamic Back-Edge Corridor |
|  - Microsecond Local Decision | (COM9)  |  - ANPR License Plate Engine  |
+-------------------------------+         |  - WhatsApp e-Challan Gateway |
                                          +---------------+---------------+
                                                          |
                                                          | Shared State
                                                          v
                                          +-------------------------------+
                                          |   Unified Streamlit Control   |
                                          |   - 30 FPS Native MJPEG HUD   |
                                          |   - Live Proximity Waveform   |
                                          |   - Boom Barrier Lockout HUD  |
                                          |   - e-Challan Legal Registry  |
                                          +-------------------------------+
```

---

## 🔌 Hardware Circuit & Wiring (ESP32 + HC-SR04)

The HC-SR04 sensor operates at **5V VCC**, while ESP32 GPIO inputs are **3.3V safe**. A **voltage divider** (1kΩ + 2kΩ) protects GPIO 27 from over-voltage.

```
       [ESP32 DevKit V1]                             [HC-SR04 Sensor]
       +-----------------+                           +----------------+
       |             VIN | =======================> | VCC (5V)       |
       |             GND | =======================> | GND            |
       |         GPIO 14 | =======================> | TRIG           |
       |                 |                          |                |
       |         GPIO 27 | <----+ [V_out ~ 3.3V]    |                |
       +-----------------+      |                   |                |
                               [R1 = 1kΩ]           |                |
                                |                   |                |
                                +------------------ | ECHO (5V Out)  |
                                |                   +----------------+
                               [R2 = 2kΩ]
                                |
                               === (GND)
```

| ESP32 Pin | Sensor Pin | Description |
| :--- | :--- | :--- |
| **V5 / VIN** | **VCC** | 5V Power Supply |
| **GND** | **GND** | Common Ground |
| **GPIO 14** | **TRIG** | Trigger Pulse Output (10 µs) |
| **GPIO 27** | **ECHO** | Voltage Divider Center (~3.3V Safe Echo Input) |

---

## 📂 Repository Structure

```
TollGuard-AI/
├── alerts/                         # Timestamped violation evidence & HSRP plate crops
├── esp32_sensor_node/              # ESP32 firmware & on-chip TinyML header
│   ├── esp32_sensor_node.ino       # Main Arduino C++ firmware
│   └── queue_tinyml_model.h        # Embedded C++ Decision Tree header
├── models/
│   └── yolov5n.onnx                # YOLOv5 Nano ONNX model (OpenCV DNN compatible)
├── classifier.py                   # Sensor ML baselines (Random Forest & SVM)
├── config.py                       # Global thresholds, PCU weights & statutory fines
├── corridor.py                     # Dynamic Back-Edge queue corridor integrity engine
├── dashboard.py                    # Unified Streamlit web control center
├── detector.py                     # YOLOv5 object detector & Ambulance insignia filter
├── export_tinyml_esp32.py          # Decision Tree trainer & C++ header code generator
├── lstm_forecaster.py              # Long Short-Term Memory (LSTM) queue forecaster
├── plate_reader.py                 # ANPR bumper localization & HSRP plate renderer
├── queue_camera.py                 # Multi-threaded 30 FPS MJPEG daemon & serial reader
├── simulate_demo.py                # Standalone simulation with lane-cutter & ambulance
├── run_dashboard.bat               # One-click launcher for People/Counter Queue mode
├── run_toll_plaza.bat              # One-click launcher for Vehicle Toll & ANPR mode
├── run_simulation.bat              # One-click launcher for simulation mode
├── requirements.txt                # Python dependencies
└── README.md                       # Complete technical documentation
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.10, 3.11, and 3.14 on Windows/Linux)
- **Arduino IDE** (if reflashing ESP32)
- USB Webcam or Smartphone with **IP Webcam** / **DroidCam**

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/kumaranurag7278-lgtm/TollGuard-AI.git
cd TollGuard-AI

# Install required dependencies
pip install -r requirements.txt
```

### 3. Launching the System

#### Mode A: Full Live Toll Plaza with ANPR & Hardware (Recommended)
Connect ESP32 via USB and double-click `run_toll_plaza.bat`, or run:
```bash
# Terminal 1: Start 30 FPS Camera & ANPR Daemon (Camera 0 or Phone RTSP/HTTP URL)
python queue_camera.py vehicle 0

# Terminal 2: Start Unified Streamlit Dashboard
python -m streamlit run dashboard.py
```
*Open your browser at `http://localhost:8501` to view the live 30 FPS stream, ultrasonic waveform, and boom barrier HUD.*

#### Mode B: Standalone Highway Simulation (No Camera/Hardware Needed)
```bash
# Terminal 1: Launch Dashboard
python -m streamlit run dashboard.py

# Terminal 2: Run Simulated Highway Traffic
python simulate_demo.py
```
*At Step 15, a lateral lane-cutter cuts into the line. The system automatically captures plate `PB 65 CD 4199`, locks the boom barrier, imposes a ₹500 fine, and generates an official e-Challan!*

---

## ⚖️ Legal & Statutory Compliance (India)

| Feature | Legal Statute | Statutory Action |
| :--- | :--- | :--- |
| **Mid-Corridor Lane Cutting** | Section 177, Motor Vehicles Act 1988 | ₹500 e-Challan & Barrier Lockout |
| **Ambulance Priority** | Section 194E, Motor Vehicles Act 1988 | Green Corridor Granted (Toll ₹0) |
| **FASTag Tag-Swap Fraud** | NHAI Toll Evasion Rule 11 & Sec 177 | 3x Penalty (₹1,350) & FASTag Blacklist |

---

## 👥 Academic Attribution & Team

**Engineering Clinic Project #190**  
**School of Engineering & Technology, CGC University Mohali**  
**Department:** Computer Science & Engineering (AI & Data Science) — CSE-Apex  
**Academic Year:** 2026–2027  
**Project Mentor:** Baljinder Kaur  

**Team Members:**
- **Anurag Kumar** — `2510003151`
- **Suraj Mandal** — `2510003166`
- **Ayush** — `2510003161`
- **Divine Diamond** — `2510003176`

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
