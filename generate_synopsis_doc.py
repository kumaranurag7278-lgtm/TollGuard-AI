import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def create_synopsis_word_document():
    doc = docx.Document()

    # Page Margins: 1 inch all around
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

    # ==============================================================================
    # HEADER SECTION
    # ==============================================================================
    header_table = doc.add_table(rows=1, cols=1)
    header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = header_table.cell(0, 0)
    set_cell_background(cell, "F4F6F9")
    
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run("School of Engineering & Technology, CGC University Mohali\n")
    r1.bold = True
    r1.font.size = Pt(14)
    r1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D) # Navy Blue
    
    r2 = p.add_run("Department of Artificial Intelligence & Data Science\n\n")
    r2.bold = True
    r2.font.size = Pt(12)
    
    r3 = p.add_run("ENGINEERING CLINIC — PROJECT SYNOPSIS\n")
    r3.bold = True
    r3.font.size = Pt(13)
    r3.font.color.rgb = RGBColor(0x8B, 0x00, 0x00) # Crimson

    doc.add_paragraph() # Spacer

    # Project Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = p_title.add_run("AI-Powered Smart Queue & Toll Enforcement System Using IoT Sensor Fusion and Edge AI\n")
    r_t.bold = True
    r_t.font.size = Pt(16)
    r_t.font.color.rgb = RGBColor(0x0A, 0x25, 0x40)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("AI-Based / IoT-Based Engineering Clinic Project — Synopsis Report")
    r_sub.italic = True
    r_sub.font.size = Pt(11)

    doc.add_paragraph()

    # Meta Table
    meta_table = doc.add_table(rows=6, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.style = 'Table Grid'
    
    meta_data = [
        ("AI / ML Techniques", "YOLOv5 Object Detection, Adaptive Centroid Tracking, Dynamic Back-Edge Corridor (Anti-Cut AI), On-Chip TinyML Decision Trees, PCU Wait-Time Estimation, and Random Forest/SVM Sensor Baseline"),
        ("IoT Hardware Used", "ESP32 DevKit V1 (38-pin), HC-SR04 Ultrasonic Sensor, 1kΩ + 2kΩ Resistor Voltage Divider, Solderless Breadboard, Jumper Wires, Micro-USB Cable, Laptop HD Camera"),
        ("Team Members", "Anurag Kumar — 2510003151\nSuraj Mandal — 2510003166\nAyush — 2510003161\nDivine Diamond — 2510003176"),
        ("Project Mentor", "Baljinder Kaur"),
        ("Department", "CSE-Apex"),
        ("Academic Year", "2026–2027")
    ]

    for idx, (label, val) in enumerate(meta_data):
        row = meta_table.rows[idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        set_cell_background(c0, "EAECEF")
        p0 = c0.paragraphs[0]
        r = p0.add_run(label)
        r.bold = True
        r.font.size = Pt(10)
        p1 = c1.paragraphs[0]
        r_val = p1.add_run(val)
        r_val.font.size = Pt(10)

    doc.add_page_break()

    # Helper function for Headings
    def add_section_heading(title):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(title)
        r.bold = True
        r.font.size = Pt(13)
        r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
        return h

    # Helper for Body Paragraphs
    def add_body(text):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(text)
        r.font.size = Pt(11)
        return p

    # 1. Abstract
    add_section_heading("1. Abstract")
    add_body(
        "Queue management is an important operational challenge across college offices, clinics, bank counters, and "
        "highway toll plazas. During peak periods, manual visual observation is inefficient, while traditional basic "
        "sensor systems that merely measure distance to classify queues as 'Short/Medium/Long' fail to provide genuine AI value "
        "because human staff can judge crowd depth at a glance. Furthermore, existing systems cannot detect behavioral queue "
        "infractions such as line-cutting or out-of-sequence bypasses."
    )
    add_body(
        "This project presents an advanced AI-Powered Customer Queue and Toll Enforcement System integrating low-cost IoT physical "
        "proximity sensing with real-time computer vision and on-chip TinyML Edge AI. The system monitors pedestrian service counters "
        "and vehicular highway toll lanes via two synchronized subsystems: an ESP32 microcontroller with an HC-SR04 ultrasonic sensor "
        "executing an on-chip TinyML Decision Tree for local congestion classification, and a laptop camera running a pretrained YOLOv5 "
        "neural network via OpenCV DNN for real-time entity tracking."
    )
    add_body(
        "The core innovation is a Dynamic Back-Edge Corridor that continuously tracks the spatial position of the legitimate last member "
        "in line. When a new entity appears ahead of the dynamic back edge rather than at the tail, the system automatically flags a "
        "mid-corridor forced-entry violation, captures cropped photographic proof, applies a statutory fine (₹500 under Section 177 of "
        "the Motor Vehicles Act), and locks the simulated boom barrier on a unified Streamlit operator dashboard. Wait times are projected "
        "using civil engineering Passenger Car Unit (PCU) service duration weighting. The entire prototype is implemented within an "
        "approximate student budget of ₹700, demonstrating an end-to-end fusion of embedded hardware, Edge AI, computer vision, and real-time web enforcement."
    )

    # 2. Introduction
    add_section_heading("2. Introduction")
    add_body(
        "Queues occur whenever the arrival rate of customers temporarily exceeds the service capacity of a service counter or toll booth. "
        "Although queues are ubiquitous, most facilities still depend on visual inspection or physical token machines, which cannot prevent "
        "line-cutting or dynamically optimize counter flow."
    )
    add_body(
        "Recent developments in IoT make microcontrollers like the ESP32 ideal for rapid prototyping because they combine a 240MHz dual-core "
        "CPU with integrated Wi-Fi and Bluetooth. Concurrently, computer vision models like YOLOv5 nano enable real-time object detection at "
        "30–40 FPS on standard consumer CPUs without requiring expensive GPU hardware."
    )
    add_body(
        "Rather than using AI merely to replicate human visual judgment, this project focuses on behavioral queue integrity: detecting spatial "
        "sequence violations that human staff miss, differentiating vehicle classes (Cars vs. Heavy Trucks) to forecast wait times realistically, "
        "and running Edge AI directly on microcontroller silicon to maintain operation even if internet connectivity drops."
    )

    # 3. Problem Statement
    add_section_heading("3. Problem Statement")
    add_body(
        "Manual monitoring of queues is labor-intensive, subjective, and prone to disputes. Meanwhile, simple sensor-only prototypes that "
        "only measure distance to classify queue size as Short/Medium/Long fail to demonstrate real AI value, as human observers can perform "
        "that estimation effortlessly. Existing solutions also suffer from lack of anti-line-cutting enforcement, naive headcount wait estimations "
        "that ignore vehicle mix, and heavy cloud latency."
    )
    add_body(
        "The specific problem addressed by this project is to design and validate an integrated IoT and Computer Vision system that enforces "
        "sequential queue discipline via dynamic corridor tracking, detects line-cutting violations with photographic evidence, predicts "
        "PCU-weighted clearance times, and executes on-chip TinyML inference on an ESP32 microcontroller within a ₹1000 budget."
    )

    # 4. Objectives
    add_section_heading("4. Objectives")
    add_body("1. To develop a low-cost IoT sensing node using an ESP32 DevKit and HC-SR04 ultrasonic sensor with a 1kΩ + 2kΩ resistor voltage divider for safe 3.3V logic level shifting.")
    add_body("2. To embed a TinyML Decision Tree model directly on the ESP32 microcontroller to classify queue states (Short, Medium, Long Wait) on-chip in microseconds.")
    add_body("3. To deploy a real-time YOLOv5 nano computer vision pipeline to detect pedestrians and vehicles at 30+ FPS, auto-assigning virtual sequential queue tokens.")
    add_body("4. To implement an Adaptive Centroid Tracker that compensates for detector dropouts using temporal motion allowance (allowed_distance = base + missed × allowance).")
    add_body("5. To enforce queue integrity using a Dynamic Back-Edge Corridor that catches line-cutters, locks the boom barrier, captures photo evidence, and computes PCU-weighted wait times on a unified Streamlit dashboard.")

    # 5. Literature Survey
    add_section_heading("5. Literature Survey / Existing Systems")
    lit_table = doc.add_table(rows=7, cols=5)
    lit_table.style = 'Table Grid'
    lit_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers = ["Approach / System", "Working Principle", "Strength", "Limitation", "Our Enhancement"]
    for i, h_text in enumerate(headers):
        cell = lit_table.rows[0].cells[i]
        set_cell_background(cell, "1B365D")
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r.font.size = Pt(9)

    survey_data = [
        ("Manual Observation", "Staff visually inspect queue length", "No hardware required", "Subjective; labor-intensive; no history", "Replaced by 24/7 automated AI monitoring"),
        ("Static Ultrasonic", "Fixed distance threshold", "Very low-cost", "Rejects real AI value; no line-cutting detection", "Fused with computer vision & dynamic corridor"),
        ("Infrared Beam Counters", "Beam interruption count", "Simple event counter", "Cannot describe queue geometry or sequence", "Continuous 2D spatial coordinate tracking"),
        ("SORT Tracking (Prior Art)", "Kalman filter + Hungarian algorithm", "High tracking precision", "Fails during temporary detector dropouts", "Adaptive Centroid Tracking with missed-frame scaling"),
        ("US Patent 10,262,328", "Dynamic queue entry determination", "Industry-validated back edge", "Expensive commercial infrastructure", "Re-engineered as a low-cost DIY edge corridor"),
        ("US Patent 10,755,107", "Virtual boundary passage lines", "Corridor security concept", "Rigid physical setup", "Flexible software-defined multi-lane boundaries")
    ]

    for row_idx, row_data in enumerate(survey_data, start=1):
        row = lit_table.rows[row_idx]
        for col_idx, text in enumerate(row_data):
            cell = row.cells[col_idx]
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(8.5)
            if row_idx % 2 == 0:
                set_cell_background(cell, "F9FAFB")

    # 6. Proposed System
    add_section_heading("6. Proposed System")
    add_body(
        "The proposed system contains four integrated layers: physical IoT sensing, Edge AI processing, Computer Vision tracking, and Streamlit "
        "operator enforcement. At the sensing layer, the HC-SR04 ultrasonic sensor measures distance. The ESP32 processes measurements locally "
        "and executes an on-chip TinyML Decision Tree. Concurrently, a laptop camera processes live video using YOLOv5 nano, passing bounding "
        "boxes to the Adaptive Centroid Tracker and Dynamic Corridor Engine."
    )
    add_body(
        "The system feeds live data into a unified Streamlit dashboard featuring an embedded 30 FPS MJPEG video stream, real-time proximity "
        "waveform graph, Boom Barrier control (Locked/Clear), PCU-weighted wait time projections, and an automated e-Challan evidence locker."
    )

    # 7. Hardware Requirements
    add_section_heading("7. Hardware Requirements & Cost Analysis")
    hw_table = doc.add_table(rows=8, cols=4)
    hw_table.style = 'Table Grid'
    hw_table.alignment = WD_TABLE_ALIGNMENT.CENTER

    hw_headers = ["Component", "Specification", "Purpose", "Actual Cost (₹)"]
    for i, h_text in enumerate(hw_headers):
        cell = hw_table.rows[0].cells[i]
        set_cell_background(cell, "1B365D")
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r.font.size = Pt(9.5)

    hw_rows = [
        ("ESP32 DevKit V1 (38-pin)", "240MHz Dual-Core Xtensa, 4MB Flash", "Edge AI inference, pulse timing, serial telemetry", "₹489"),
        ("HC-SR04 Ultrasonic Sensor", "40kHz Ultrasonic, 2cm–400cm range", "Queue proximity distance measurement", "₹69"),
        ("Resistor Voltage Divider", "1kΩ and 2kΩ metal film resistors", "5V to 3.3V logic level shifting on Echo pin", "₹4"),
        ("Solderless Breadboard", "30-Row compact prototype board", "Firm hardware mounting without soldering", "₹85"),
        ("Jumper Wires", "Male-to-Male (4 wires)", "Single-side breadboard routing", "₹30"),
        ("USB Data Cable", "Micro-USB to USB-A data-sync cable", "5V laptop power and COM9 serial upload", "Owned / ₹0"),
        ("Webcam", "Integrated 720p HD Laptop Camera", "YOLOv5 video acquisition at 30 FPS", "Owned / ₹0")
    ]

    for row_idx, row_data in enumerate(hw_rows, start=1):
        row = hw_table.rows[row_idx]
        for col_idx, text in enumerate(row_data):
            cell = row.cells[col_idx]
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9)
            if row_idx % 2 == 0:
                set_cell_background(cell, "F9FAFB")

    add_body("Total Prototype Hardware Expenditure: ₹677 (Well within the ₹1000 student project budget).")

    # 8. AI/ML Stack
    add_section_heading("8. Software and AI/ML Stack")
    add_body("• Embedded Edge AI: C++ / Arduino IDE / arduino-cli compiling queue_tinyml_model.h directly to ESP32 flash memory.")
    add_body("• Computer Vision: Python 3.14, OpenCV 5.0 DNN, YOLOv5 nano ONNX (pretrained on COCO classes: person, car, bus, truck, motorcycle).")
    add_body("• Tracking & Mathematics: NumPy, SciPy (Euclidean distance association matrices and temporal motion allowance scaling).")
    add_body("• Streaming Server: Python ThreadingHTTPServer delivering 30 FPS MJPEG multipart video on port 5001 directly into the browser.")
    add_body("• Web Dashboard: Streamlit 1.64.0 (Boom barrier control, live distance waveform, PCU wait calculation, evidence locker).")
    add_body("• Machine Learning Benchmark: scikit-learn (Random Forest: 99.67% accuracy vs. SVM: 97.33% accuracy).")

    # 9. Expected Outcomes & Applications
    add_section_heading("9. Expected Outcomes & Applications")
    add_body("• Operational Dual-Domain System: Validated for both pedestrian service counters and highway automated toll plazas (FASTag lanes).")
    add_body("• Autonomous Violation Enforcement: Automatically catches line-cutters, snaps timestamped evidence photos, and applies ₹500 fines.")
    add_body("• Embedded Edge AI: Executes real-time TinyML inference on ESP32 silicon independently of cloud or Wi-Fi.")
    add_body("• Real-World Applications: Highway toll plazas, university examination/fee counters, hospital registration desks, and bank teller lines.")

    # 10. References
    add_section_heading("10. References")
    add_body("[1] L. Breiman, 'Random Forests,' Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.")
    add_body("[2] C. Cortes and V. Vapnik, 'Support-Vector Networks,' Machine Learning, vol. 20, pp. 273–297, 1995.")
    add_body("[3] J. Redmon et al., 'You Only Look Once: Unified, Real-Time Object Detection,' IEEE CVPR, 2016.")
    add_body("[4] A. Bewley et al., 'Simple Online and Realtime Tracking (SORT),' IEEE ICIP, 2016.")
    add_body("[5] US Patent 10,262,328, 'Dynamic Queue Entry Point Determination and Monitoring,' assigned to Disney Enterprises, Inc., Apr. 16, 2019.")
    add_body("[6] US Patent 10,755,107, 'Passage Detection System Using Virtual Boundary Lines,' Aug. 25, 2020.")
    add_body("[7] Indian Motor Vehicles Act, Section 177: General Provision for Punishment of Offences (Lane Discipline).")
    add_body("[8] Espressif Systems, 'ESP32 Series Datasheet & Technical Reference Manual,' v4.2, 2024.")

    doc.save(os.path.join("D:\\New folder", "PROJECT_SYNOPSIS_REPORT.docx"))
    print("[DOCX Generator] Successfully generated D:\\New folder\\PROJECT_SYNOPSIS_REPORT.docx")

if __name__ == "__main__":
    create_synopsis_word_document()
