@echo off
echo Starting Adaptive GPU Scheduler API...
echo.
cd /d "%~dp0"
pip install -r requirements.txt -q
python start.py
