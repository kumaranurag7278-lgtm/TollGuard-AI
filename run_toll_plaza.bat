@echo off
cd /d "%~dp0"
title AI Toll Plaza & ANPR Enforcement System
echo ============================================================
echo Starting AI Camera Engine in VEHICLE mode with ANPR...
echo ============================================================
start /B python queue_camera.py vehicle 0
echo ============================================================
echo Starting Unified Streamlit Dashboard...
echo ============================================================
python -m streamlit run dashboard.py
pause
