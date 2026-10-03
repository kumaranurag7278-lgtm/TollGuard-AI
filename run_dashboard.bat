@echo off
cd /d "%~dp0"
title AI Toll & Queue Unified Enforcement System
echo ============================================================
echo Starting AI Camera Engine in background...
echo ============================================================
start /B python queue_camera.py people 0
echo ============================================================
echo Starting Unified Streamlit Dashboard...
echo ============================================================
python -m streamlit run dashboard.py
pause
