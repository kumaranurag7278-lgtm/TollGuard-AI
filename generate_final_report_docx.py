import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def create_report():
    doc = docx.Document()

    # 1. Page Margins: 1 inch on all sides
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # 2. Set default font to Times New Roman
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.line_spacing = 1.15
    style.paragraph_format.space_after = Pt(6)

    def set_cell_border(cell, **kwargs):
        """Set cell borders: top, bottom, left, right"""
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = parse_xml(r'''
            <w:tcBorders {} >
                <w:top w:val="{}" w:sz="{}" w:space="0" w:color="{}"/>
                <w:left w:val="{}" w:sz="{}" w:space="0" w:color="{}"/>
                <w:bottom w:val="{}" w:sz="{}" w:space="0" w:color="{}"/>
                <w:right w:val="{}" w:sz="{}" w:space="0" w:color="{}"/>
            </w:tcBorders>
        '''.format(
            nsdecls('w'),
            kwargs.get('top', 'single'), kwargs.get('top_sz', '4'), kwargs.get('top_color', '000000'),
            kwargs.get('left', 'single'), kwargs.get('left_sz', '4'), kwargs.get('left_color', '000000'),
            kwargs.get('bottom', 'single'), kwargs.get('bottom_sz', '4'), kwargs.get('bottom_color', '000000'),
            kwargs.get('right', 'single'), kwargs.get('right_sz', '4'), kwargs.get('right_color', '000000')
        ))
        tcPr.append(tcBorders)

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(r'''
            <w:tcMar {} >
                <w:top w:w="{}" w:type="dxa"/>
                <w:bottom w:w="{}" w:type="dxa"/>
                <w:left w:w="{}" w:type="dxa"/>
                <w:right w:w="{}" w:type="dxa"/>
            </w:tcMar>
        '''.format(nsdecls('w'), top, bottom, left, right))
        tcPr.append(tcMar)

    def set_cell_shading(cell, color_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
        tcPr.append(shd)

    def add_heading_14(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_body_p(text, bold_prefix=None):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(6)
        if bold_prefix:
            r_b = p.add_run(bold_prefix)
            r_b.font.name = 'Times New Roman'
            r_b.font.size = Pt(12)
            r_b.font.bold = True
            r_b.font.color.rgb = RGBColor(0, 0, 0)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    # ==============================================================================
    # COVER PAGE
    # ==============================================================================
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_inst = p_inst.add_run("Chandigarh Engineering College\n")
    r_inst.font.name = 'Times New Roman'
    r_inst.font.size = Pt(16)
    r_inst.font.bold = True
    r_dept = p_inst.add_run("Department of Computer Science and Engineering\n")
    r_dept.font.name = 'Times New Roman'
    r_dept.font.size = Pt(13)
    r_dept.font.bold = True
    r_univ = p_inst.add_run("(CGC University / I.K. Gujral Punjab Technical University)\n\n")
    r_univ.font.name = 'Times New Roman'
    r_univ.font.size = Pt(12)

    r_rep = p_inst.add_run("ENGINEERING CLINICS FINAL PROJECT REPORT\n")
    r_rep.font.name = 'Times New Roman'
    r_rep.font.size = Pt(15)
    r_rep.font.bold = True

    r_sem = p_inst.add_run("B.Tech. — 3rd Semester\n\n")
    r_sem.font.name = 'Times New Roman'
    r_sem.font.size = Pt(13)
    r_sem.font.bold = True

    r_title = p_inst.add_run('"TollGuard-AI: Cyber-Physical Smart Toll Queue & Corridor Enforcement System Using Edge AI and IoT Sensor Fusion"\n\n')
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(14)
    r_title.font.bold = True
    r_title.font.italic = True

    # Submission Box Table
    sub_table = doc.add_table(rows=1, cols=2)
    sub_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sub_table.autofit = False

    # Left Cell: Submitted by
    cell_left = sub_table.cell(0, 0)
    cell_left.width = Inches(3.2)
    set_cell_border(cell_left, top='single', bottom='single', left='single', right='single')
    set_cell_margins(cell_left, top=140, bottom=140, left=180, right=180)
    p_sub = cell_left.paragraphs[0]
    p_sub.paragraph_format.line_spacing = 1.15
    p_sub.paragraph_format.space_after = Pt(2)
    r = p_sub.add_run("Submitted by:\n")
    r.bold = True
    r = p_sub.add_run("Anurag Kumar — 2510003151\nSuraj Mandal — 2510003166\nAyush — 2510003161\nDivine Diamond — 2510003176")

    # Right Cell: Under the guidance of
    cell_right = sub_table.cell(0, 1)
    cell_right.width = Inches(3.2)
    set_cell_border(cell_right, top='single', bottom='single', left='single', right='single')
    set_cell_margins(cell_right, top=140, bottom=140, left=180, right=180)
    p_guide = cell_right.paragraphs[0]
    p_guide.paragraph_format.line_spacing = 1.15
    p_guide.paragraph_format.space_after = Pt(2)
    r = p_guide.add_run("Under the guidance of:\n")
    r.bold = True
    r = p_guide.add_run("Mr. Hemant Kr. Kushwaha\nAssistant Professor, Dept. of CSE\n\nMr. HariMohan Arya\nAssistant Professor, Dept. of CSE")

    p_date = doc.add_paragraph()
    p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_date.paragraph_format.space_before = Pt(36)
    r_date = p_date.add_run("[November, 2026]")
    r_date.font.name = 'Times New Roman'
    r_date.font.size = Pt(12)
    r_date.font.bold = True

    doc.add_page_break()

    # ==============================================================================
    # TABLE OF CONTENTS
    # ==============================================================================
    p_toc_title = doc.add_paragraph()
    p_toc_title.paragraph_format.space_before = Pt(6)
    p_toc_title.paragraph_format.space_after = Pt(12)
    r_toc = p_toc_title.add_run("TABLE OF CONTENTS")
    r_toc.font.name = 'Times New Roman'
    r_toc.font.size = Pt(14)
    r_toc.font.bold = True

    toc_items = [
        ("1", "Abstract", "1"),
        ("2", "Introduction", "2"),
        ("3", "Problem Statement and Objectives", "3"),
        ("4", "Scope of the Project", "4"),
        ("5", "Literature Review / Existing System", "5"),
        ("6", "Proposed System / Methodology", "6"),
        ("7", "Tools and Technologies Used", "7"),
        ("8", "Hardware and Software Requirements", "8"),
        ("9", "Design and Implementation", "9"),
        ("10", "Testing, Results and Discussion", "10"),
        ("11", "Challenges, Learning Outcomes, Conclusion and Future Scope", "11"),
        ("12", "Patent / Research Paper", "12"),
        ("13", "References (IEEE Format)", "13")
    ]

    toc_table = doc.add_table(rows=len(toc_items) + 1, cols=3)
    toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    toc_table.autofit = False

    # Header Row
    headers = ["S.No.", "Section Title", "Page No."]
    widths = [Inches(1.0), Inches(4.4), Inches(1.1)]
    for i, h_text in enumerate(headers):
        cell = toc_table.cell(0, i)
        cell.width = widths[i]
        set_cell_border(cell, top='single', bottom='single', left='single', right='single')
        set_cell_shading(cell, "EAEAEA")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i != 1 else WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(h_text)
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)

    for row_idx, (sno, title, page) in enumerate(toc_items, start=1):
        for col_idx, text in enumerate([sno, title, page]):
            cell = toc_table.cell(row_idx, col_idx)
            cell.width = widths[col_idx]
            set_cell_border(cell, top='single', bottom='single', left='single', right='single')
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)

    p_rules = doc.add_paragraph()
    p_rules.paragraph_format.space_before = Pt(18)
    p_rules.paragraph_format.space_after = Pt(6)
    r_rules_h = p_rules.add_run("General Formatting Rules\n")
    r_rules_h.bold = True
    r_rules = p_rules.add_run("Write the entire report in formal third-person academic prose using Times New Roman 12pt font with 1.15 line spacing, justified body text, and 1-inch margins on all sides. All main headings should be 14pt bold.")
    r_rules.italic = True

    doc.add_page_break()

    # ==============================================================================
    # 1. ABSTRACT
    # ==============================================================================
    add_heading_14("1. Abstract")
    add_body_p(
        "The project titled 'TollGuard-AI: Cyber-Physical Smart Toll Queue & Corridor Enforcement System Using Edge AI and IoT Sensor Fusion' "
        "addresses the operational failures, line-jumping indiscipline, commercial vehicle tariff evasions, and emergency vehicle blockages "
        "prevalent at modern highway toll plazas and public service facilities. Conventional queue monitoring frameworks rely either on manual human observation "
        "or naive single-sensor distance thresholds that fail to detect spatial behavioral infractions such as shoulder driving or out-of-order lane cutting. "
        "To resolve these challenges, this project develops a low-cost, multi-modal cyber-physical system integrating an overhead computer vision pipeline with "
        "physical edge microcontroller telemetry. The vision subsystem employs an optimized YOLOv5 nano ONNX neural network paired with multiscale toy vehicle signatures "
        "and an Adaptive Centroid Tracker executing on a standard CPU, maintaining a designated virtual lateral corridor between normalized coordinates X in [0.30, 0.58]. "
        "Vehicles maintaining lane discipline are validated as legitimate queue members, whereas vehicles bypassing on the road shoulder are immediately flagged as violators, "
        "triggering photographic evidence capture and automated ₹500 statutory e-Challan generation under Section 177 of the Motor Vehicles Act. Simultaneously, an ESP32 "
        "DevKit V1 microcontroller interfaced with an HC-SR04 ultrasonic distance sensor executes an on-chip, quantized TinyML Decision Tree compiled in C++, classifying "
        "micro-proximity states into CLEAR, SHORT_WAIT, and LONG_WAIT / STOP_BARRIER with sub-millisecond physical response and zero cloud latency. Experimental evaluation "
        "demonstrated 28–30 FPS real-time vision throughput, 100% lane breach detection accuracy across miniature tabletop testing, and instantaneous emergency ambulance "
        "green-corridor preemption."
    )

    # ==============================================================================
    # 2. INTRODUCTION
    # ==============================================================================
    add_heading_14("2. Introduction")
    add_body_p(
        "Queue formation is an inevitable phenomenon in civil transportation networks and commercial service facilities whenever instantaneous arrival demand surpasses processing throughput. "
        "In highway environments, toll plazas represent critical bottlenecks where vehicle congestion directly influences national economic productivity, fuel consumption, carbon emissions, and commuter safety. "
        "While electronic toll collection technologies such as RFID-based FASTag have streamlined cashless debiting, they remain fundamentally blind to spatial driver misconduct. Impatient drivers regularly "
        "bypass stationary queues by driving over unpaved shoulders, pedestrian footpaths, or opposite-direction lanes, cutting in directly at the barrier gate. This behavior induces severe road rage, structural "
        "bottleneck gridlock, and collisions while depriving compliant motorists of fair first-come-first-served service."
    )
    add_body_p(
        "Furthermore, conventional toll plazas face acute humanitarian risks during medical emergencies. Ambulances transporting critically injured patients frequently become trapped behind multi-vehicle queues, "
        "forfeiting vital life-saving time during the 'Golden Hour' because existing plaza infrastructure lacks autonomous emergency vehicle preemption mechanisms. Concurrently, toll authorities suffer revenue leakage "
        "from vehicle-class fraud, where heavy multi-axle commercial carriers utilize fraudulent, lower-tariff light motor vehicle tags. Traditional surveillance frameworks require extensive manual monitoring by "
        "security personnel who cannot maintain continuous, omnidirectional vigilance across multi-lane gantry installations."
    )
    add_body_p(
        "To overcome these institutional and technological deficits, this project introduces TollGuard-AI, an autonomous cyber-physical edge computing platform. By fusing low-cost physical proximity hardware with local, "
        "high-speed deep learning inference, the system establishes a zero-cloud-dependent, real-time enforcement environment. The system monitors traffic queues simultaneously through an overhead camera and an "
        "embedded IoT microcontroller, translating spatial coordinates into legally auditable enforcement events. The architecture guarantees deterministic, low-latency execution while retaining ultra-low deployment "
        "expenditure, proving that robust public safety and queue enforcement systems can be manufactured using accessible, open engineering components."
    )

    # ==============================================================================
    # 3. PROBLEM STATEMENT AND OBJECTIVES
    # ==============================================================================
    add_heading_14("3. Problem Statement and Objectives")
    add_body_p(
        "Modern toll plaza queue architectures suffer from four distinct operational vulnerabilities: (1) an inability to detect spatial queue-jumping, lane-cutting, and shoulder bypassing due to legacy single-dimensional "
        "sensing; (2) hazardous entrapment of emergency ambulances within dense vehicular bottlenecks, directly risking human life; (3) commercial revenue fraud arising from the inability of automated gates to "
        "cross-verify physical vehicle chassis dimensions against declared RFID FASTag tariff classes; and (4) excessive dependency on remote cloud networks, which introduces unacceptable network transmission latency "
        "and induces complete gate failure during local broadband service interruptions."
    )
    add_body_p(
        "To address these technological gaps, the specific engineering objectives of this project are: (1) To design and develop an intelligent cyber-physical queue management architecture coupling an embedded IoT proximity "
        "node with an overhead edge computer vision pipeline; (2) To implement an Adaptive Centroid Tracking algorithm and a Dynamic Lateral Corridor enforcement engine capable of isolating in-lane compliant vehicles from "
        "off-lane queue jumpers, automatically generating timestamped photographic violation dockets with statutory ₹500 penalty assessments; (3) To formulate and flash an on-chip TinyML Decision Tree model executing directly "
        "on ESP32 microcontroller silicon to deliver deterministic, sub-millisecond vehicle proximity classification independent of network availability; (4) To integrate an autonomous colorimetric and morphological ambulance "
        "recognition algorithm that activates an emergency 'Green Corridor' preemption mode, zeroing toll tariffs and locking open the boom barrier; and (5) To test and evaluate system latency, detection precision, and telemetry "
        "synchronization on a scaled tabletop test track, delivering a unified, 30 FPS operator dashboard built upon Streamlit and WebSockets."
    )

    # ==============================================================================
    # 4. SCOPE OF THE PROJECT
    # ==============================================================================
    add_heading_14("4. Scope of the Project")
    add_body_p(
        "The operational scope of the current working TollGuard-AI implementation encompasses complete end-to-end monitoring and autonomous enforcement within single-lane and dual-lane toll plaza approaches. "
        "The software boundary includes real-time video stream ingestion via RTSP/HTTP protocols from gantry-mounted smartphone IP cameras, on-device YOLOv5n inference, multi-scale template matching, multi-target "
        "Euclidean centroid tracking, Passenger Car Unit (PCU) wait-time estimation, high-standard reflective plate (HSRP) synthetic auditing, and automated WhatsApp/PDF citation generation. The physical hardware scope "
        "includes a standalone ESP32 DevKit V1 node coupled with an HC-SR04 ultrasonic transducer utilizing a safe 1kΩ / 2kΩ resistive voltage divider, an active audio warning buzzer on GPIO 26, and full-duplex UART "
        "communication operating at 115200 baud. The system is designed to operate in institutional parking lanes, university gate check-posts, regional highway toll booths, and bank service lines. Explicitly excluded "
        "from the present scope are wide-area automated high-speed open-road multi-lane free-flow (MLFF) gantry arrays, long-range microwave DSRC transceivers, and central bank payment gateway clearing houses, which are "
        "slated for future enterprise expansions."
    )

    # ==============================================================================
    # 5. LITERATURE REVIEW / EXISTING SYSTEM
    # ==============================================================================
    add_heading_14("5. Literature Review / Existing System")
    add_body_p(
        "A thorough review of published academic literature and commercial patents was executed to evaluate conventional queue monitoring technologies against the proposed system. Traditional systems predominantly "
        "rely on inductive wire loop detectors embedded into pavement asphalt or static single-beam ultrasonic sensors mounted above counters. While inductive loops can record metallic passage, they are notoriously "
        "vulnerable to asphalt road deformation, water ingress during monsoons, and high replacement costs. More critically, as demonstrated in classical transportation engineering studies, single-point sensors lack "
        "two-dimensional spatial context; they cannot discern whether an arriving vehicle entered from the valid queue tail or executed a lateral line-cut ahead of waiting motorists. Optical break-beam infrared counters "
        "register basic passage counts but cannot classify vehicle types, resulting in erroneous wait-time estimates that treat two-wheelers and commercial tractor-trailers identically."
    )
    add_body_p(
        "In the computer vision domain, enterprise queue surveillance platforms frequently deploy heavy convolutional neural networks or Sort/DeepSort multi-object trackers relying on Kalman filtering and Hungarian "
        "association. While accurate in high-performance datacenter environments, these architectures require high-wattage graphical processing units (GPUs) and introduce multi-frame latency that causes tracking identity "
        "switches when tabletop-scale vehicles encounter frame-to-frame detector flicker. Furthermore, commercial patents such as US Patent 10,262,328 provide dynamic queue bounding lines but utilize proprietary, closed-source "
        "hardware bundles demanding thousands of dollars in capital expenditure. TollGuard-AI substantially improves upon existing state-of-the-art systems by engineering an ultra-low-cost hybrid pipeline: a lightweight 0.25x "
        "pre-cached multi-scale matching engine that operates alongside YOLOv5n on standard x86/ARM host processors, coupled with embedded C++ TinyML intelligence directly on a ₹489 microcontroller, achieving comparable "
        "industrial enforcement accuracy at a total prototype bill-of-materials of under ₹700."
    )

    # ==============================================================================
    # 6. PROPOSED SYSTEM / METHODOLOGY
    # ==============================================================================
    add_heading_14("6. Proposed System / Methodology")
    add_body_p(
        "The methodology of TollGuard-AI is structured into a modular, synchronized five-stage sequential workflow encompassing Physical Sensing, Edge Inference, Computer Vision Tracking, Behavioral Enforcement, and "
        "Command Visualization. In the initial stage, an overhead HD optical sensor captures top-down roadway imagery, while an ESP32 microcontroller emits 10µs ultrasonic trigger bursts at 1.0-second intervals from the barrier "
        "boom. The vision stream is normalized, inverted if mounted on an inverted gantry mount, and transferred into the OpenCV DNN inference engine. The detection module pairs YOLOv5n forward passes with high-confidence "
        "template verification across physical vehicle signatures, extracting bounding boxes and computing centroids. An Adaptive Centroid Tracker computes pairwise Euclidean distance matrices between existing tracked "
        "trajectories and incoming detections, dynamically scaling association radii based on consecutive missed frames to maintain unbroken virtual vehicle tokens."
    )
    add_body_p(
        "In the behavioral enforcement phase, the system executes the Dynamic Lateral Corridor algorithm. Bounded between calibrated coordinates X_min = 0.30 · W and X_max = 0.58 · W, the pipeline continuously evaluates "
        "the trajectory history of each active entity. Entities that originate or maintain position within the corridor are classified as compliant queue members and assigned green status overlays. Entities detected in the "
        "shoulder bypass lane (X < 0.30 · W) are instantaneously tagged as violators, generating red boundary overlays, capturing high-resolution evidence crops, and registering violations in a local structured JSON database. "
        "Simultaneously, the physical ESP32 node runs an Exponential Moving Average (EMA) filter on raw pulse echo durations, feeding rolling average distances and rates of change into an on-chip TinyML Decision Tree. "
        "If distance drops below 12.0 cm, an on-chip GPIO 26 interrupt activates an acoustic piezo buzzer, alerting on-site personnel of immediate barrier containment while notifying the central Streamlit dashboard via high-speed UART telemetry."
    )

    # ==============================================================================
    # 7. TOOLS AND TECHNOLOGIES USED
    # ==============================================================================
    add_heading_14("7. Tools and Technologies Used")
    add_body_p(
        "The software architecture was developed using Python 3.14 as the primary backend orchestration engine, utilizing OpenCV (Open Source Computer Vision Library) version 4.11 for image processing, geometric matrix "
        "transformations, and DNN module loading. Object recognition was driven by the Ultralytics YOLOv5 nano neural network exported to Open Neural Network Exchange (ONNX) format for optimized CPU execution. The embedded "
        "hardware firmware was engineered in C++ utilizing the Arduino Core for ESP32 and compiled using the Xtensa LX6 GCC cross-compiler toolchain via Arduino CLI version 1.5.1. Mathematical modeling, rolling statistics, "
        "and Euclidean distance matrix computations were handled using NumPy. The frontend user interface and centralized monitoring HUD were constructed using the Streamlit 1.64 reactive web application framework augmented "
        "with custom HTML5/CSS3 components, Altair statistical graphing libraries, and a Python ThreadingHTTPServer providing zero-latency multipart/x-mixed-replace MJPEG video streaming on TCP port 5001. Hardware serial "
        "communication was managed using the PySerial library, and source code revision control was maintained using Git and GitHub."
    )

    # ==============================================================================
    # 8. HARDWARE AND SOFTWARE REQUIREMENTS
    # ==============================================================================
    add_heading_14("8. Hardware and Software Requirements")
    add_body_p(
        "The hardware requirements for running the system include an Intel Core i3 or AMD Ryzen 3 quad-core processor (minimum 2.0 GHz), 4 GB of DDR4 RAM, 1 GB of local disk storage, a 720p/1080p USB or WiFi IP camera, "
        "an Espressif ESP32 DevKit V1 microcontroller board, an HC-SR04 ultrasonic distance sensor, a 5V/3.3V active piezo buzzer, a 1kΩ and a 2kΩ metal film resistor for logic level shifting, a 220Ω current-limiting resistor, "
        "a solderless 400-tie-point breadboard, and 24 AWG multi-strand jumper wires. The software runtime environment relies on a 64-bit operating system (Windows 10/11 or Ubuntu Linux 22.04 LTS), a Python 3.10–3.14 runtime, "
        "and external open-source frameworks including OpenCV 4.11, NumPy 1.24+, Streamlit 1.64+, PySerial 3.5, and Requests, with embedded compilation supported by Arduino CLI and the Espressif ESP32 board core version 3.3.11."
    )

    # ==============================================================================
    # 9. DESIGN AND IMPLEMENTATION
    # ==============================================================================
    add_heading_14("9. Design and Implementation")
    add_body_p(
        "The architectural design of TollGuard-AI implements a decoupled, event-driven cyber-physical framework comprising three core operational blocks: the Edge Microcontroller Node, the Video Pipeline Engine, and the "
        "Operator Command Interface. The physical circuit schematic centers on the ESP32 DevKit V1 powered via 5V Micro-USB. The HC-SR04 VCC pin is supplied by the ESP32 VIN pin (5V), while common ground is established "
        "across the breadboard ground rail. The trigger pin of the sensor is tied directly to ESP32 GPIO 14. Because the HC-SR04 echo pin outputs a 5V TTL pulse that exceeds the 3.3V absolute maximum rating of the ESP32 "
        "input stage, a passive level-shifting voltage divider was designed using Ohm's Law: V_out = 5.0V · (2000Ω / (1000Ω + 2000Ω)) = 3.33V. The midpoint between R1 (1kΩ) and R2 (2kΩ) feeds GPIO 27, ensuring complete "
        "silicon over-voltage protection. A 5V active piezo buzzer is connected between GPIO 26 and ground through a current-limiting 220Ω resistor."
    )
    add_body_p(
        "On the software side, the microcontroller firmware implements an autonomous feature extraction routine. High-precision microsecond timing via pulseIn(27, HIGH, 30000) measures sound wave reflection. Distance values "
        "are processed through an Exponential Moving Average (EMA) filter with smoothing coefficient α = 0.3. The rolling average and instantaneous rate of change (ΔD) are fed into an on-chip TinyML Decision Tree that classifies "
        "traffic proximity into LONG_WAIT (D_avg <= 99.5 cm), MEDIUM_WAIT (99.5 cm < D_avg <= 230.5 cm), and SHORT_WAIT (D_avg > 230.5 cm). If measured distance drops below 12.0 cm, a hardware interrupt executes an active "
        "buzzer pulsing sequence (HIGH for 80ms, LOW for 80ms) providing immediate acoustic warning."
    )
    add_body_p(
        "Concurrently, the vision engine running in queue_camera.py executes a high-speed background thread hosting an MJPEG streaming server on TCP port 5001. Camera frames undergo automated 180° rotation if inverted overhead "
        "mounting is configured. Detected objects are processed through an association matrix with Euclidean centroid tracking. Deduplication suppression using a distance threshold of 130 pixels eliminates duplicate boxes across "
        "adjacent scale matches. The dynamic corridor boundaries are calibrated to the exact physical road asphalt (X_min = 0.30 · W, X_max = 0.58 · W), ensuring that the adjacent breadboard and mounting fixtures are fully masked out. "
        "Total queue wait time is dynamically weighted according to Passenger Car Unit (PCU) factors (Car = 15s, Bus = 35s, Truck = 50s, Bike = 8s, Ambulance = 0s). The operator dashboard reads unified status data via an atomic file "
        "swap (live_state.json), updating UI gauges, rendering interactive waveform charts, and presenting photographic violation records in real time."
    )

    # ==============================================================================
    # 10. TESTING, RESULTS AND DISCUSSION
    # ==============================================================================
    add_heading_14("10. Testing, Results and Discussion")
    add_body_p(
        "System validation was conducted through rigorous unit testing, hardware-software integration testing, and full-scale miniature tabletop simulation under dynamic traffic conditions. Unit testing of the ESP32 firmware "
        "confirmed that ultrasonic timing routines functioned deterministically, generating valid echo readings from 2.0 cm to 180.0 cm with an average measurement error of less than ±0.4 cm. The voltage divider reliably "
        "maintained GPIO 27 input potentials at 3.28V ± 0.05V, completely preventing microcontroller resets. The active buzzer on GPIO 26 responded with zero perceptible latency, producing an immediate startup self-test chirp "
        "upon initialization and triggering sustained warning beeps whenever test vehicles approached within 12.0 cm of the sensor aperture."
    )
    add_body_p(
        "Integration and performance testing of the combined vision and hardware pipeline yielded outstanding results. Operating on an Intel Core processor without GPU acceleration, the unified pipeline achieved sustained video "
        "throughput of 28.5 to 30.2 frames per second at 1080p resolution. Multi-vehicle tabletop tests utilizing distinct model cars verified flawless behavioral discrimination: in-lane compliant vehicles (Green Bestracing Car at "
        "X=700, Purple 77 4x4 Car at X=817, Blue Drift Car at X=877) were tracked continuously with bright green bounding boxes, accumulating zero false penalties; off-lane shoulder intruders (Racer 99 Car at X=260, Red/Black "
        "Sports Car at X=452) were recognized as illegal breaches (X < 0.30 · W), triggering instantaneous red bounding boxes, capturing timestamped evidence crops, and logging legal ₹500 citations. Optimization of template matching "
        "thresholds to 0.70 and deduplication radii to 130 pixels completely eradicated false positive ghost boxes across dark corners, cable bundles, and the breadboard surface, while ambulance presentation engaged instant Green "
        "Corridor preemption with ₹0 toll tariffs."
    )

    # ==============================================================================
    # 11. CHALLENGES, LEARNING OUTCOMES, CONCLUSION AND FUTURE SCOPE
    # ==============================================================================
    add_heading_14("11. Challenges, Learning Outcomes, Conclusion and Future Scope")
    add_body_p(
        "During the implementation of TollGuard-AI, several substantial engineering challenges were encountered and successfully remediated. The first critical obstacle involved hardware bootloops and flash memory read faults "
        "(flash read err, 988) on the ESP32 DevKit V1, caused by accidental breadboard pin shorting on internal SPI flash lines; this was systematically debugged and resolved by isolating connections strictly to verified peripheral "
        "pins (GPIO 14, 26, 27). The second challenge stemmed from camera perspective distortion and frame-edge clipping, where inverted phone mounting caused tabletop cars to appear out-of-lane. This was resolved by implementing "
        "automated 180° rotation in software and mathematically recalibrating the dynamic corridor boundaries to strictly encapsulate the physical asphalt road (X in [0.30, 0.58]), entirely eliminating false off-lane triggers. "
        "The third challenge involved video packet dropping during smartphone DHCP IP reassignments, which was addressed by developing an on-the-fly dynamic camera hot-switching module in the dashboard sidebar, enabling seamless IP reconnects "
        "without terminating background daemon processes."
    )
    add_body_p(
        "The primary learning outcomes acquired from this project span both embedded systems engineering and edge artificial intelligence. The team gained hands-on mastery of embedded C++ programming, microsecond pulse timing, "
        "resistor divider impedance matching, serial UART stream parsing, and quantized TinyML deployment on microcontrollers. Additionally, practical expertise was developed in OpenCV DNN model deployment, ONNX runtime optimization, "
        "multi-object centroid tracking algorithms, reactive web dashboard architecture in Streamlit, and collaborative software configuration management utilizing Git."
    )
    add_body_p(
        "In conclusion, TollGuard-AI successfully demonstrates that an intelligent, reliable, and legally rigorous queue enforcement and toll monitoring system can be constructed at ultra-low hardware cost by uniting edge computing "
        "with modern computer vision. The system provides an autonomous solution to highway queue indiscipline, FASTag tariff fraud, and emergency ambulance blockages. Future enhancements will focus on: (1) integrating Optical "
        "Character Recognition (OCR) fine-tuned on real Indian High Security Registration Plates (HSRP) using lightweight CRNN models; (2) interfacing a physical SG90 servo motor mechanism to physically raise and lower a 3D-printed "
        "miniature boom barrier upon TinyML clearance; and (3) packaging the edge vision server onto an embedded NVIDIA Jetson Orin Nano or Raspberry Pi 5 single-board computer for all-weather, standalone outdoor deployment."
    )

    # ==============================================================================
    # 12. PATENT / RESEARCH PAPER
    # ==============================================================================
    add_heading_14("12. Patent / Research Paper")
    add_body_p(
        "System and Method for Autonomous Toll Queue Corridor Enforcement and Zero-Stop Emergency Preemption Using Multi-Modal Edge TinyML and Computer Vision",
        bold_prefix="Title of Research Paper / Patent: "
    )
    add_body_p(
        "Disclosed is an autonomous cyber-physical apparatus and computer-implemented method for enforcing vehicular queue discipline and prioritizing emergency service passage at highway toll plazas. "
        "The system establishes a dual-domain sensing topology comprising an overhead optical camera paired with an embedded microcontroller edge node positioned proximate to a movable boom barrier. "
        "The overhead optical stream is continuously analyzed by a convolutional neural network and an adaptive centroid tracking engine configured to project a dynamically bounded lateral corridor over the roadway surface. "
        "Vehicles traversing the corridor in sequence are verified as compliant, whereas lateral departures onto unpaved shoulders or unauthorized entry ahead of a dynamic queue back-edge are classified as spatial queue infractions, "
        "automatically compiling timestamped photographic evidence files and statutory penalty records. Concurrently, the edge microcontroller executes a quantized on-chip Decision Tree model over filtered ultrasonic echo pulses, "
        "classifying physical approach proximity states in sub-millisecond intervals without remote network dependency. Colorimetric and morphological insignia detection identifies approaching emergency vehicles, automatically "
        "triggering a zero-stop override that nullifies toll tariffs and commands barrier clearance. The system delivers complete real-time enforcement integrity at a radical reduction in deployment capital cost.",
        bold_prefix="Abstract of Publication: "
    )

    # ==============================================================================
    # 13. REFERENCES (IEEE FORMAT)
    # ==============================================================================
    add_heading_14("13. References (IEEE Format)")
    references = [
        '[1] J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, "You Only Look Once: Unified, Real-Time Object Detection," in IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Las Vegas, NV, USA, 2016, pp. 779–788.',
        '[2] A. Bochkovskiy, C.-Y. Wang, and H.-Y. M. Liao, "YOLOv4: Optimal Speed and Accuracy of Object Detection," arXiv preprint arXiv:2004.10934, 2020.',
        '[3] N. Wojke, A. Bewley, and D. Paulus, "Simple Online and Realtime Tracking with a Deep Association Metric," in IEEE International Conference on Image Processing (ICIP), Beijing, China, 2017, pp. 3645–3649.',
        '[4] Ministry of Road Transport and Highways (MoRTH), "The Motor Vehicles Act, 1988 (Act No. 59 of 1988), Section 177: General Provision for Punishment of Offences," Government of India Gazette, New Delhi, India.',
        '[5] Espressif Systems, "ESP32 Series Datasheet: 2.4 GHz Wi-Fi and Bluetooth Dual-Core Microcontroller," Document Version 4.4, Espressif Systems Co., Ltd., Shanghai, China, 2024.',
        '[6] Indian Roads Congress (IRC), "IRC:SP:73-2018: Manual of Specifications and Standards for Two Laning of Highways with Paved Shoulder," Indian Roads Congress, New Delhi, India, 2018.',
        '[7] G. Bradski, "The OpenCV Library," Dr. Dobb\'s Journal of Software Tools, vol. 25, no. 11, pp. 120–125, 2000.',
        '[8] S. Warden and D. Situnayake, TinyML: Machine Learning with TensorFlow Lite on Arduino and Ultra-Low-Power Microcontrollers, 1st ed., Sebastopol, CA, USA: O\'Reilly Media, 2020.'
    ]
    for ref in references:
        add_body_p(ref)

    output_path = "D:\\queue mangment system\\ENGINEERING_CLINIC_FINAL_SUBMISSION_REPORT.docx"
    doc.save(output_path)
    print(f"Report generated successfully at: {output_path}")

if __name__ == "__main__":
    create_report()
