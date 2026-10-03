# School of Engineering & Technology, CGC University Mohali
### Department of Artificial Intelligence & Data Science
**ENGINEERING CLINIC — PROJECT SYNOPSIS**

## AI-Powered Smart Queue & Toll Enforcement System Using IoT Sensor Fusion and Edge AI

| Attribute | Details |
| :--- | :--- |
| **AI / ML Techniques** | YOLOv5 Object Detection, Adaptive Centroid Tracking, Dynamic Back-Edge Corridor (Anti-Cut AI), On-Chip TinyML Decision Trees, PCU Wait-Time Estimation, and Random Forest/SVM Sensor Baseline |
| **IoT Hardware Used** | ESP32 DevKit V1 (38-pin), HC-SR04 Ultrasonic Distance Sensor, 1kΩ + 2kΩ Voltage Divider, Solderless Breadboard, Jumper Wires, Micro-USB Cable, Laptop HD Camera |
| **Team Members** | **Anurag Kumar** — 2510003151<br>**Suraj Mandal** — 2510003166<br>**Ayush** — 2510003161<br>**Divine Diamond** — 2510003176 |
| **Project Mentor** | Baljinder Kaur |
| **Department** | CSE-Apex |
| **Academic Year** | 2026–27 |

---

### 1. Abstract
Traditional queue monitoring relies on manual visual observation or basic single-sensor distance thresholds that merely state whether a line is short or long. Such basic approaches fail to provide genuine AI value because human staff can easily estimate queue depth at a glance. Furthermore, existing systems cannot detect behavioral queue infractions such as line-cutting, out-of-order service bypasses, or vehicle-class clearance bottlenecks.

This project presents an advanced **AI-Powered Customer Queue and Toll Enforcement System** integrating low-cost IoT physical proximity sensing with real-time computer vision and on-chip TinyML Edge AI. The system monitors service counters (pedestrian domain) and highway toll lanes (vehicular domain) via two synchronized subsystems:
1. **IoT Edge AI Subsystem:** An ESP32 microcontroller interfaced with an HC-SR04 ultrasonic distance sensor executes a quantized **TinyML Decision Tree directly on-chip** (Xtensa 240MHz dual-core CPU) to classify real-time arrival congestion into *Short, Medium, or Long Wait* states in microseconds without cloud latency.
2. **Computer Vision & Behavioral AI Subsystem:** A stationary camera feed processes frames using a pretrained **YOLOv5 nano neural network** (via OpenCV DNN) to detect pedestrians and vehicles. A custom **Adaptive Centroid Tracker** resolves detector flicker by dynamically scaling matching thresholds ($\text{allowed\_dist} = \text{base} + \text{missed} \times \text{allowance}$). Sequential virtual tokens are assigned automatically.
3. **Dynamic Back-Edge Corridor Enforcement:** The core behavioral innovation continuously tracks the spatial position of the legitimate last queue member. When a new entity appears ahead of the dynamic back edge rather than at the tail, the system immediately flags a **mid-corridor forced-entry violation**, crops photographic proof, applies a statutory fine (₹500 under Section 177 of the Motor Vehicles Act), and locks the simulated boom barrier on a unified Streamlit operator dashboard.

Wait times are projected using civil engineering **Passenger Car Unit (PCU)** service duration weighting rather than naive headcounts. The entire prototype is implemented within an accessible budget of ₹800–₹1000, demonstrating an end-to-end fusion of embedded hardware, Edge AI, computer vision, and real-time web enforcement.

---

### 2. Introduction
Queues occur whenever the arrival rate of customers temporarily exceeds the service capacity of a counter or service point. Although queues are common, many small organizations still depend on visual observation or physical token machines, which cannot prevent line-cutting or dynamically optimize counter flow.

Recent developments in IoT make microcontrollers like the ESP32 ideal for rapid prototyping because they combine a 240MHz dual-core CPU with integrated Wi-Fi and Bluetooth. Concurrently, computer vision models like YOLOv5 nano enable real-time object detection at 30–40 FPS on standard consumer CPUs without requiring expensive GPU hardware.

Rather than using AI merely to replicate human visual judgment, this project focuses on behavioral queue integrity: detecting spatial sequence violations that human staff miss, differentiating vehicle classes (Cars vs. Heavy Trucks) to forecast wait times realistically, and running Edge AI directly on microcontroller silicon to maintain operation even if internet connectivity drops.

---

### 3. Problem Statement
Existing low-cost queue monitoring systems suffer from four critical deficiencies:
1. **Lack of Behavioral AI:** Measuring distance to classify "Short/Medium/Long" fails to demonstrate AI value, as human staff can visually evaluate queue size instantly.
2. **Inability to Prevent Queue Violations:** In busy queues and highway toll bottlenecks, impatient individuals cut in laterally ahead of waiting patrons. Existing sensor systems lack spatial awareness to flag out-of-sequence entries.
3. **Naive Clearance Time Estimation:** Systems that count raw entities treat heavy multi-axle freight trucks identically to small hatchbacks, producing inaccurate wait-time predictions.
4. **Hardware-Cloud Latency & Fragility:** Purely cloud-dependent IoT systems fail whenever network connectivity drops.

**Project Problem:** To design, build, and validate an integrated IoT and Computer Vision system that enforces sequential queue discipline via dynamic corridor tracking, detects line-cutting violations with photographic evidence, predicts PCU-weighted clearance times, and executes on-chip TinyML inference on an ESP32 microcontroller within a ₹1000 student budget.

---

### 4. Objectives
1. **IoT Edge AI Sensing Node:** Design a 3.3V-safe ESP32 and HC-SR04 ultrasonic circuit using a $1\text{k}\Omega + 2\text{k}\Omega$ resistor voltage divider, executing on-chip TinyML queue classification directly on microcontroller hardware.
2. **Real-Time Object Detection & Virtual Token Dispensing:** Implement an OpenCV DNN YOLOv5 nano pipeline to detect pedestrians and vehicles at 30+ FPS, auto-assigning sequential queue tokens without physical ticket machines.
3. **Adaptive Centroid Tracking:** Develop an adaptive tracking algorithm compensating for detector dropouts using temporal motion allowance ($\text{dist} = \text{base} + \text{missed} \times \text{allowance}$).
4. **Dynamic Corridor & Anti-Cut Enforcement:** Formulate dynamic back-edge tracking to identify mid-corridor lateral insertions, capture timestamped photographic evidence, and calculate automated fine penalties.
5. **PCU Wait-Time Prediction & Load Balancing:** Implement civil engineering Passenger Car Unit service duration weighting, multi-lane load balancing, and a unified Streamlit operator control dashboard.

---

### 5. Literature Survey & Comparative Analysis

| Approach | Working Principle | Strengths | Limitations | Our System Enhancement |
| :--- | :--- | :--- | :--- | :--- |
| **Manual Observation** | Staff visually inspect queue length | No hardware required | Labor intensive; subjective; no history | Replaced by 24/7 automated AI monitoring |
| **Static Ultrasonic Distance** | Fixed distance threshold | Inexpensive | Rejects real AI value; cannot detect line jumping | Combined with computer vision & dynamic corridor |
| **Infrared Beam Counter** | Beam break event count | Simple hardware | Cannot measure queue geometry or queue order | Continuous spatial coordinate tracking |
| **Bluetooth / Wi-Fi Sniffing** | RSSI MAC address tracking | Broad area coverage | Unreliable; requires active device radios | Vision + ultrasonic sensor fusion |
| **SORT Tracker (Prior Art)** | Kalman filter + Hungarian | High tracking precision | Fails during extended detection flickers | **Adaptive Centroid Tracking** with missed-frame scaling |
| **US Patent 10,262,328** | Dynamic queue entry point | Industry-validated back edge | High-cost commercial implementation | Re-engineered as a **low-cost DIY edge corridor** |
| **US Patent 10,755,107** | Passage detection boundaries | Virtual corridor concept | Rigid commercial infrastructure | Flexible software-defined multi-lane boundaries |

---

### 6. Proposed System Architecture

The proposed system contains four integrated layers:
1. **Physical Sensing Layer:** ESP32 reads HC-SR04 echo pulse duration through a safe voltage divider.
2. **On-Chip Edge AI Layer:** ESP32 executes an embedded C++ decision tree (`queue_tinyml_model.h`) classifying queue congestion in microseconds.
3. **Computer Vision & Corridor Layer:** Pretrained YOLOv5 nano detects entities. The adaptive tracker maintains token order, while the dynamic back-edge corridor catches mid-lane lateral insertions and captures cropped violation evidence.
4. **Presentation & Control Layer:** Unified Streamlit dashboard provides high-speed 30 FPS video streaming, live proximity waveform graph, Boom Barrier lockout, PCU wait-time projections, and e-Challan generation.

---

### 7. Hardware Requirements & Cost Analysis

| Component | Specification | Purpose | Actual Cost (₹) |
| :--- | :--- | :--- | :--- |
| **ESP32 DevKit V1 (38-pin)** | 240MHz Dual-Core Xtensa, 4MB Flash | Edge AI inference, pulse timing, serial telemetry | ₹489 |
| **HC-SR04 Sensor** | 40kHz Ultrasonic, 2cm–400cm range | Queue proximity distance measurement | ₹69 |
| **Resistors ($R_1, R_2$)** | $1\text{k}\Omega$ and $2\text{k}\Omega$ metal film | 5V to 3.3V logic level shifting on Echo pin | ₹4 |
| **Breadboard** | 30-Row solderless breadboard | Component mounting | ₹85 |
| **Jumper Wires** | Male-to-Male (4 wires) | Circuit routing | ₹30 |
| **USB Cable** | Micro-USB to USB-A data-sync cable | 5V power and COM9 programming | Owned / ₹0 |
| **Webcam** | Integrated 720p HD Laptop Camera | Computer vision video acquisition | Owned / ₹0 |
| **Total Hardware Cost** | — | **Complete Physical Prototype** | **₹677** |

---

### 8. Software and AI/ML Stack

| Category | Technology | Function in System |
| :--- | :--- | :--- |
| **Edge AI Firmware** | C++ / Arduino IDE / `arduino-cli` | HC-SR04 pulse measurement, EMA smoothing, TinyML inference |
| **Embedded Model** | `queue_tinyml_model.h` | On-chip decision tree compiled into microcontroller instructions |
| **Core Vision Engine** | Python 3.14, OpenCV 5.0 DNN | YOLOv5 nano ONNX inference, image transformations, HUD overlays |
| **Tracking Engine** | NumPy, SciPy | Euclidean distance association matrix, dynamic thresholding |
| **Streaming Pipeline** | Python `ThreadingHTTPServer` | High-speed 30 FPS MJPEG multipart video server on port 5001 |
| **User Interface** | Streamlit 1.64.0 | Single-screen toll operator HUD, boom barrier control, live graph |
| **ML Benchmark** | scikit-learn 1.9.1 | Random Forest (99.67%) vs. SVM (97.33%) baseline comparison |
| **Time-Series Forecaster**| Recurrent Normalized Gradient Descent | $+5\text{m}, +10\text{m}, +15\text{m}$ autoregressive wait-time prediction |

---

### 9. Expected Outcomes & Applications
* Fully functioning dual-mode prototype operating across both **Pedestrian Counters** and **Highway Toll Plazas**.
* Autonomous line-cutting detection flagging violators and saving photographic evidence to disk.
* Real-time boom barrier lockout enforcing ₹500 statutory penalties.
* Validated edge AI execution running directly on the ESP32 microcontroller CPU.
* Butter-smooth 30 FPS video streaming and live sensor waveform graphing on a single unified web dashboard.
* Comprehensive prototype delivered well within the ₹1000 student budget limit (Actual: ₹677).

**Applications:**
* Automated Highway Toll Plazas (FASTag bottleneck lane enforcement)
* Bank & Financial Service Counters (fair token queueing)
* Hospital Triage & Outpatient Registration Desks
* College Examination & Fee Registration Counters

---

### 10. References
1. L. Breiman, "Random Forests," *Machine Learning*, vol. 45, no. 1, pp. 5–32, 2001.
2. C. Cortes and V. Vapnik, "Support-Vector Networks," *Machine Learning*, vol. 20, pp. 273–297, 1995.
3. J. Redmon et al., "You Only Look Once: Unified, Real-Time Object Detection," *IEEE CVPR*, 2016.
4. A. Bewley, Z. Ge, L. Ott, F. Ramos, and B. Upcroft, "Simple Online and Realtime Tracking (SORT)," *IEEE ICIP*, 2016.
5. US Patent 10,262,328, "Dynamic Queue Entry Point Determination and Monitoring," assigned to Disney Enterprises, Inc., Apr. 16, 2019.
6. US Patent 10,755,107, "Passage Detection System Using Virtual Boundary Lines," Aug. 25, 2020.
7. Indian Motor Vehicles Act, Section 177: General Provision for Punishment of Offences (Lane Discipline and Traffic Disruption).
8. Espressif Systems, "ESP32 Series Datasheet & Technical Reference Manual," v4.2, 2024.
