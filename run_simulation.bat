@echo off
cd /d "%~dp0"
title AI Toll Queue Simulator
echo ============================================================
echo Running vehicle queue and lane-cutting simulation in: %CD%
echo ============================================================
python simulate_demo.py
pause
