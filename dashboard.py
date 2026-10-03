import os
import json
import time
import urllib.parse
from datetime import datetime
import streamlit as st
import pandas as pd
from PIL import Image

import config

st.set_page_config(
    page_title="AI Smart Queue & Toll Enforcement Center",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .barrier-locked {
        background-color: #4a1515;
        border: 2px solid #ff4d4d;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        color: #ff9999;
    }
    .barrier-clear {
        background-color: #133926;
        border: 2px solid #2ecc71;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        color: #a3e4d7;
    }
    .video-container {
        border-radius: 10px;
        overflow: hidden;
        border: 2px solid #30363d;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    }
    .hsrp-badge {
        display: inline-block;
        background: #ffffff;
        color: #111111;
        font-family: 'Consolas', 'Courier New', monospace;
        font-weight: 900;
        font-size: 1.25rem;
        padding: 4px 14px;
        border-radius: 6px;
        border: 2px solid #222222;
        letter-spacing: 2px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.5);
        margin: 6px 0;
    }
    .hsrp-badge-comm {
        display: inline-block;
        background: #f1c40f;
        color: #111111;
        font-family: 'Consolas', 'Courier New', monospace;
        font-weight: 900;
        font-size: 1.25rem;
        padding: 4px 14px;
        border-radius: 6px;
        border: 2px solid #222222;
        letter-spacing: 2px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.5);
        margin: 6px 0;
    }
</style>
""", unsafe_allow_html=True)

def load_live_state():
    if os.path.exists(config.LIVE_STATE_FILE):
        try:
            with open(config.LIVE_STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "timestamp": time.time(),
        "mode": "vehicle",
        "active_count": 0,
        "breakdown": {},
        "wait_seconds": 0,
        "corridor_active": False,
        "back_edge_y": None,
        "front_entity": None,
        "total_violations_today": 0,
        "esp32_connected": False,
        "esp32_distance": 400.0,
        "esp32_tinyml": "SHORT_WAIT"
    }

def load_violations():
    if os.path.exists(config.VIOLATIONS_FILE):
        try:
            with open(config.VIOLATIONS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

# Initialize distance history in session_state for live sparkline graph
if "dist_history" not in st.session_state:
    st.session_state.dist_history = [400.0] * 20

state = load_live_state()
violations = load_violations()

# Append live distance to graph history
live_dist = state.get("esp32_distance", 400.0)
st.session_state.dist_history.append(live_dist)
if len(st.session_state.dist_history) > 25:
    st.session_state.dist_history.pop(0)

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/traffic-light.png", width=64)
    st.title("Control Center")

    active_mode = state.get("mode", "vehicle")
    st.info(f"Active Vision Mode: **{active_mode.upper()}**\n\n*(Change in terminal: `python queue_camera.py people` or `vehicle`)*")

    st.divider()
    st.subheader("Physical Hardware (ESP32)")
    esp_conn = state.get("esp32_connected", False)
    if esp_conn:
        st.success(f"🟢 **ESP32 Node:** Connected (COM9)\n\n"
                   f"📏 **Distance:** `{live_dist:.1f} cm`\n\n"
                   f"🧠 **TinyML Edge AI:** `{state.get('esp32_tinyml', 'STANDBY')}`")
    else:
        st.warning("🟡 **ESP32 Node:** Standby / Connecting...")

    st.divider()
    st.subheader("ANPR / ALPR Engine")
    st.success("🔍 **Plate Recognition:** ACTIVE\n\n"
               "🇮🇳 **Format:** Indian Standard HSRP\n\n"
               "⚖️ **Legal Enforcement:** Sec 177 MV Act")

    st.divider()
    st.subheader("🧪 Live AI Demonstrations")
    sim_ambulance = st.toggle("🚨 Simulate Ambulance Arrival", value=False, help="Simulates emergency ambulance detection with automatic Green Corridor preemption")
    sim_fastag_fraud = st.toggle("🕵️ Simulate FASTag Swap Fraud", value=False, help="Simulates Class IV multi-axle truck using a Class I car FASTag")

    st.divider()
    auto_refresh = st.checkbox("Auto-Sync Telemetry (2s)", value=True)

# ==============================================================================
# TOP BAR: GLOBAL METRICS
# ==============================================================================
st.title("🚦 AI Smart Queue Management & Toll Enforcement Center")
st.caption("Engineering Clinic Project #190 | Unified Computer Vision + IoT Hardware Edge AI + ANPR Plate Recognition")

m1, m2, m3, m4 = st.columns(4)
active_cnt = state.get("active_count", 0)
wait_sec = state.get("wait_seconds", 0)
wait_str = f"{wait_sec // 60}m {wait_sec % 60}s"
corridor_active = state.get("corridor_active", False)

with m1:
    st.metric("Live Queue Occupancy", f"{active_cnt} in Queue", delta=f"{active_mode.capitalize()} Mode")
with m2:
    st.metric("PCU-Weighted Wait Time", wait_str, help="Clearance time weighted by PCU vehicle/person service duration")
with m3:
    status_label = "ENFORCING" if corridor_active else "STANDBY (<3 in line)"
    st.metric("Corridor Integrity", status_label, delta="Anti-cut Active" if corridor_active else "Low-occupancy Guard")
with m4:
    total_fines = len(violations) * config.VIOLATION_PENALTY
    st.metric("Violations Logged", f"{len(violations)} Cases", delta=f"₹{total_fines} Penalties")

st.divider()

# ==============================================================================
# MAIN SECTION: 30 FPS EMBEDDED STREAM (LEFT) + REAL-TIME HARDWARE & HUD (RIGHT)
# ==============================================================================
col_video, col_hardware = st.columns([1.3, 1])

with col_video:
    st.subheader("📹 Live 30 FPS AI Vision Feed & Dynamic Corridor")
    # Native High-Speed MJPEG stream directly from port 5001 (Zero stutter, butter smooth!)
    mjpeg_html = """
    <div class="video-container">
        <img src="http://localhost:5001/video_feed" style="width:100%; display:block;" onerror="this.onerror=null; this.src='https://placehold.co/640x480/202020/white?text=Waiting+for+Camera+Engine...';">
    </div>
    """
    st.markdown(mjpeg_html, unsafe_allow_html=True)
    st.caption(f"YOLOv5 Nano + Adaptive Centroid Tracking + ANPR License Plate Recognition ({active_mode.upper()} Mode)")

with col_hardware:
    st.subheader("📡 Live ESP32 Hardware & Toll Barrier HUD")
    
    # Real-time Ultrasonic Waveform Graph
    st.line_chart(st.session_state.dist_history, height=160, use_container_width=True)
    st.caption("Live HC-SR04 Proximity Waveform (Distance in cm)")

    # Boom Barrier HUD
    front = state.get("front_entity")

    if sim_ambulance or (front and (front.get("is_emergency") or front.get("class") == "AMBULANCE")):
        # Emergency Vehicle Green Wave Priority (Statutory Section 194E)
        amb_plate = front.get("license_plate", "PB 65 AM 1080") if front else "PB 65 AM 1080"
        amb_token = front.get("token", "08") if front else "08"
        st.markdown(f"""
        <div style="background-color: #0b3d1b; border: 2px solid #00ff7f; border-radius: 8px; padding: 16px; text-align: center; color: #b3ffd9; box-shadow: 0 0 15px rgba(0,255,127,0.3);">
            <h3 style="margin:0; color:#00ff7f;">🚨 GREEN CORRIDOR: EMERGENCY AMBULANCE</h3>
            <div style="margin: 8px 0;">
                <span class="hsrp-badge">🇮🇳 {amb_plate}</span>
            </div>
            <p><b>Vehicle #{amb_token} (EMERGENCY AMBULANCE)</b> — Life Safety Priority Granted</p>
            <p style="font-size:1.15rem; color:#00ff7f; margin:4px 0;"><b>Toll Fare: ₹0.00 (100% EXEMPTED) | BOOM BARRIER: AUTO-LIFTED 🟢</b></p>
            <p style="font-size:0.85rem; color:#ccffeb;">Statutory Right-of-Way: <b>Section 194E, Motor Vehicles Act 1988</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🟢 Resume Normal Toll Flow", use_container_width=True):
            st.success("Ambulance cleared through Green Corridor. Barrier returned to standard state.")

    elif sim_fastag_fraud or (front and front.get("fastag_mismatch")):
        # FASTag Tag-Swap / Classification Fraud
        fraud_plate = front.get("license_plate", "PB 10 TR 8841") if front else "PB 10 TR 8841"
        fraud_token = front.get("token", "04") if front else "04"
        st.markdown(f"""
        <div style="background-color: #4a2d0b; border: 2px solid #ff9900; border-radius: 8px; padding: 16px; text-align: center; color: #ffdd99; box-shadow: 0 0 15px rgba(255,153,0,0.3);">
            <h3 style="margin:0; color:#ffaa00;">⚠️ FASTag FRAUD DETECTED: TAG MISMATCH!</h3>
            <div style="margin: 8px 0;">
                <span class="hsrp-badge-comm">🇮🇳 {fraud_plate}</span>
            </div>
            <p><b>Visual AI Detection: HEAVY MULTI-AXLE TRUCK</b></p>
            <p><b>Scanned FASTag RFID: CLASS I (HATCHBACK CAR)</b></p>
            <p style="font-size:1.15rem; color:#ffcc66; margin:4px 0;"><b>Tax Evasion Penalty: ₹1,350.00 (3x Freight Rate)</b></p>
            <p style="font-size:0.85rem; color:#ffe6b3;">FASTag Blacklisted & Reported under NHAI Evasion Rule 11 & Sec 177 MV Act.</p>
        </div>
        """, unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("💳 Collect Evasion Fine & Release", type="primary", use_container_width=True):
                st.success("Penalty ₹1,350 collected. Truck released.")
        with b2:
            if st.button("🚨 Seize FASTag & Escalate", use_container_width=True):
                st.warning("Tag ID blacklisted in central NPCI / NHAI registry.")

    elif front:
        is_violator = front.get("is_violator", False)
        t_num = front.get("token", "N/A")
        c_name = front.get("class", "Entity").upper()
        plate_str = front.get("license_plate", "PB 65 CD 4199" if is_violator else "PB 65 AK 1024")
        plate_type = front.get("plate_type", "PRIVATE (WHITE)")
        badge_class = "hsrp-badge-comm" if "COMMERCIAL" in plate_type else "hsrp-badge"
        
        if is_violator:
            st.markdown(f"""
            <div class="barrier-locked">
                <h3 style="margin:0;">🚨 BOOM BARRIER: LOCKED (OFFENSE DETECTED)</h3>
                <div style="margin: 8px 0;">
                    <span class="{badge_class}">🇮🇳 {plate_str}</span>
                </div>
                <p><b>Vehicle #{t_num} ({c_name})</b> - {front.get('violation_reason')}</p>
                <p style="font-size:1.15rem; color:#ffb3b3; margin:4px 0;"><b>Penalty Due: ₹{config.BASE_TOLL_FARE + config.VIOLATION_PENALTY}</b> (Toll ₹{config.BASE_TOLL_FARE} + Fine ₹{config.VIOLATION_PENALTY})</p>
                <p style="font-size:0.85rem; color:#ffcccc;">Statutory Code: <b>{config.PENALTY_CODE}</b> (Motor Vehicles Act)</p>
            </div>
            """, unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            with b1:
                if st.button("💳 Collect Fine & Clear", type="primary", use_container_width=True):
                    st.success("Penalty ₹500 & Toll ₹90 collected. Barrier lifted!")
            with b2:
                if st.button("📜 Dispute / Escalate", use_container_width=True):
                    st.warning("Case forwarded to Highway Police Patrol.")
        else:
            st.markdown(f"""
            <div class="barrier-clear">
                <h3 style="margin:0;">🟢 BOOM BARRIER: CLEAR (PASS GRANTED)</h3>
                <div style="margin: 8px 0;">
                    <span class="{badge_class}">🇮🇳 {plate_str}</span>
                </div>
                <p><b>Vehicle #{t_num} ({c_name})</b> - Verified Legitimate Queue Member</p>
                <p style="font-size:1.1rem; margin:4px 0;">Standard Toll Fare: <b>₹{config.BASE_TOLL_FARE}</b> (FASTag Auto-Debit)</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🟢 Open Barrier", use_container_width=True):
                st.success("Vehicle cleared through toll barrier.")
    else:
        st.info("No vehicle currently at the front barrier/counter.")

st.divider()

# ==============================================================================
# BOTTOM SECTION: MULTI-LANE DIVERSION & ANPR EVIDENCE
# ==============================================================================
b_col1, b_col2 = st.columns([1, 1.25])

with b_col1:
    st.subheader("🔀 Smart Traffic Diversion Recommendation")
    l1_wait = wait_sec
    l2_wait = max(20, int(wait_sec * 0.5) + 10)
    l3_wait = int(wait_sec * 1.5) + 30
    best = min([("Lane 1 (Live AI)", l1_wait), ("Lane 2 (FASTag Fast)", l2_wait), ("Lane 3 (Freight)", l3_wait)], key=lambda x: x[1])
    
    st.success(f"🌟 **Smart Highway Signage:** Divert incoming traffic to **{best[0]}** (~{best[1]}s wait)")
    st.dataframe(pd.DataFrame([
        {"Lane": "Lane 1 (Live AI)", "Queue": active_cnt, "Wait": f"{l1_wait}s", "Status": "Optimal" if best[0].startswith("Lane 1") else "Normal"},
        {"Lane": "Lane 2 (FASTag Fast)", "Queue": max(1, active_cnt // 2), "Wait": f"{l2_wait}s", "Status": "Optimal" if best[0].startswith("Lane 2") else "Normal"},
        {"Lane": "Lane 3 (Freight)", "Queue": active_cnt + 2, "Wait": f"{l3_wait}s", "Status": "Congested"}
    ]), hide_index=True, use_container_width=True)

with b_col2:
    st.subheader("📸 ANPR License Plate & Violation Evidence")
    if violations:
        last_v = violations[-1]
        v_col1, v_col2 = st.columns([1.1, 1.2])
        
        # Vehicle photographic proof
        with v_col1:
            img_file = os.path.join(config.ALERTS_DIR, last_v.get("snapshot", ""))
            if os.path.exists(img_file):
                st.image(img_file, use_container_width=True, caption=f"Vehicle Proof: Token #{last_v.get('id')}")
            else:
                st.info("Awaiting vehicle snapshot...")

        # Number plate crop & metadata
        with v_col2:
            plate_img_file = os.path.join(config.ALERTS_DIR, last_v.get("plate_snapshot", ""))
            if os.path.exists(plate_img_file):
                st.image(plate_img_file, use_container_width=True, caption="Detected HSRP License Plate")
            
            plate_number = last_v.get("license_plate", "PB 65 CD 4199")
            st.markdown(f"**License Plate:** `{plate_number}`")
            st.write(f"**Offense:** `{last_v.get('violation_type')}`")
            st.write(f"**Timestamp:** {last_v.get('timestamp')}")
            st.write(f"**Fine Imposed:** **₹{last_v.get('penalty_inr')}** ({config.PENALTY_CODE})")
            
            # e-Challan text generator for instant download
            echallan_text = f"""==============================================================
      PUNJAB / CHANDIGARH HIGHWAY TRAFFIC POLICE
        AUTOMATED TOLL PLAZA & QUEUE ENFORCEMENT
                  OFFICIAL E-CHALLAN SLIP
==============================================================
Challan Ref No : PB-CHAL-{last_v.get('id')}-{int(time.time())}
Date & Time    : {last_v.get('timestamp')}
Enforcing Unit : CCTV AI Vision Node #190 (CGC Mohali NH-5)
Vehicle Class  : {last_v.get('class_name', 'Car').upper()}
License Plate  : {plate_number} (RTO SAS Nagar Mohali)
Offense Reason : {last_v.get('violation_type')}
Statute Breached: Section 177, Motor Vehicles Act 1988
Base Toll Fare : INR {config.BASE_TOLL_FARE}.00
Fine Penalty   : INR {last_v.get('penalty_inr')}.00
TOTAL PAYABLE  : INR {config.BASE_TOLL_FARE + last_v.get('penalty_inr')}.00
Status         : {last_v.get('status', 'UNPAID')}
==============================================================
Notice: Failure to pay within 15 days will result in FASTag 
blacklist and summons under Section 177 of the MV Act.
==============================================================
"""
            # Direct WhatsApp e-Challan Dispatch (No QR code, pure direct message payload)
            wa_message = f"""*HIGHWAY POLICE E-CHALLAN NOTICE*
Reference: PB-CHAL-{last_v.get('id')}
Vehicle Plate: {plate_number}
Offense: {last_v.get('violation_type')}
Location: NH-5 Toll Plaza Lane 1 (CGC Mohali)
Fine Imposed: INR {last_v.get('penalty_inr')}.00
Legal Authority: Section 177, Motor Vehicles Act 1988
Status: PENDING
Camera Proof: CCTV Node #190 Evidence Captured
Please clear statutory penalty within 15 days."""
            
            wa_encoded = urllib.parse.quote(wa_message)
            wa_url = f"https://wa.me/?text={wa_encoded}"
            
            st.markdown(f"""
            <div style="background-color: #0b2e1a; border: 1px solid #25d366; border-radius: 6px; padding: 10px; margin-top: 10px; margin-bottom: 10px;">
                <p style="margin:0 0 4px 0; color:#25d366; font-size:0.9rem;"><b>📲 Automated WhatsApp Police Dispatch:</b></p>
                <p style="font-size:0.8rem; color:#d4fcdb; margin:0 0 8px 0;">Channel: Secure RTO SMS Gateway | Linked Mobile (+91 98765-XXXXX)</p>
                <a href="{wa_url}" target="_blank" style="display:block; text-align:center; background-color:#25d366; color:#0e1117; font-weight:bold; font-size:0.88rem; padding:8px; border-radius:5px; text-decoration:none;">📲 Dispatch Notice to Owner on WhatsApp</a>
            </div>
            """, unsafe_allow_html=True)

            st.download_button(
                label="📄 Download Official e-Challan Receipt",
                data=echallan_text,
                file_name=f"eChallan_{plate_number.replace(' ', '_')}_{last_v.get('id')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("No line-cutting violations flagged today. Queue discipline maintained!")

st.divider()

# ==============================================================================
# SECTION: COMPREHENSIVE E-CHALLAN & LICENSE PLATE AUDIT REGISTRY
# ==============================================================================
st.subheader("📑 Automated e-Challan & License Plate Registry")
if violations:
    table_data = []
    for idx, v in enumerate(violations):
        table_data.append({
            "Case ID": f"#{idx + 1:03d}",
            "Token": f"#{v.get('id')}",
            "Vehicle Type": str(v.get('class_name', 'Car')).upper(),
            "License Plate": v.get('license_plate', 'PB 65 CD 4199'),
            "Violation Type": v.get('violation_type'),
            "Fine (INR)": f"₹{v.get('penalty_inr')}",
            "Timestamp": v.get('timestamp'),
            "Status": v.get('status', 'UNPAID')
        })
    df_violations = pd.DataFrame(table_data)
    st.dataframe(df_violations, hide_index=True, use_container_width=True)
else:
    st.caption("No violations recorded in the system yet.")

if auto_refresh:
    time.sleep(2.0)
    st.rerun()
