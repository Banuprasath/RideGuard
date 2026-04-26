@echo off
title Motorcycle Accident Detection System - Installer
color 0A

echo.
echo =============================================================
echo   MOTORCYCLE ACCIDENT DETECTION SYSTEM - AUTO INSTALLER
echo   Final Year Project - MCA Semester 4
echo =============================================================
echo.

:: ─────────────────────────────────────────
:: STEP 1 - Check Python version
:: ─────────────────────────────────────────
echo [STEP 1] Checking Python version...
python --version 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Python is NOT installed or not in PATH.
    echo.
    echo Please install Python 3.7 from:
    echo https://www.python.org/downloads/release/python-3712/
    echo.
    echo IMPORTANT: During install, CHECK "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Python found.
echo.

:: ─────────────────────────────────────────
:: STEP 2 - Upgrade pip
:: ─────────────────────────────────────────
echo [STEP 2] Upgrading pip...
python -m pip install --upgrade pip
echo.

:: ─────────────────────────────────────────
:: STEP 3 - Install all Python libraries
:: ─────────────────────────────────────────
echo [STEP 3] Installing required Python libraries...
echo This may take 5-10 minutes depending on internet speed.
echo.

pip install ultralytics
if errorlevel 1 ( echo [WARN] ultralytics install had issues, continuing... )

pip install opencv-python
if errorlevel 1 ( echo [WARN] opencv-python install had issues, continuing... )

pip install pygame
if errorlevel 1 ( echo [WARN] pygame install had issues, continuing... )

pip install numpy
if errorlevel 1 ( echo [WARN] numpy install had issues, continuing... )

pip install requests
if errorlevel 1 ( echo [WARN] requests install had issues, continuing... )

pip install pyserial
if errorlevel 1 ( echo [WARN] pyserial install had issues, continuing... )

pip install pandas
if errorlevel 1 ( echo [WARN] pandas install had issues, continuing... )

pip install scikit-learn
if errorlevel 1 ( echo [WARN] scikit-learn install had issues, continuing... )

pip install matplotlib
if errorlevel 1 ( echo [WARN] matplotlib install had issues, continuing... )

pip install python-dotenv
if errorlevel 1 ( echo [WARN] python-dotenv install had issues, continuing... )

echo.
echo [OK] All Python libraries installed.
echo.

:: ─────────────────────────────────────────
:: STEP 4 - Verify key imports
:: ─────────────────────────────────────────
echo [STEP 4] Verifying installations...
echo.

python -c "import cv2; print('  opencv-python  : OK - version', cv2.__version__)"
python -c "import pygame; print('  pygame         : OK - version', pygame.__version__)"
python -c "import numpy; print('  numpy          : OK - version', numpy.__version__)"
python -c "import requests; print('  requests       : OK')"
python -c "import serial; print('  pyserial       : OK')"
python -c "import pandas; print('  pandas         : OK - version', pandas.__version__)"
python -c "import sklearn; print('  scikit-learn   : OK - version', sklearn.__version__)"
python -c "import matplotlib; print('  matplotlib     : OK - version', matplotlib.__version__)"
python -c "from ultralytics import YOLO; print('  ultralytics    : OK')"

echo.

:: ─────────────────────────────────────────
:: STEP 5 - Check required project files
:: ─────────────────────────────────────────
echo [STEP 5] Checking required project files...
echo.

if exist "best.pt" (
    echo   best.pt              : FOUND
) else (
    echo   best.pt              : MISSING - Copy YOLOv8 model file here
)

if exist "accidents.csv" (
    echo   accidents.csv        : FOUND
) else (
    echo   accidents.csv        : MISSING
)

if exist ".env" (
    echo   .env                 : FOUND
) else (
    echo   .env                 : MISSING - Copy .env file here
)

if exist "Merging_module_3.py" (
    echo   Merging_module_3.py  : FOUND
) else (
    echo   Merging_module_3.py  : MISSING
)

if exist "Rear_Location.py" (
    echo   Rear_Location.py     : FOUND
) else (
    echo   Rear_Location.py     : MISSING
)

if exist "emergency_alert.py" (
    echo   emergency_alert.py   : FOUND
) else (
    echo   emergency_alert.py   : MISSING
)

if exist "hotspot_detector.py" (
    echo   hotspot_detector.py  : FOUND
) else (
    echo   hotspot_detector.py  : MISSING
)

echo.

:: ─────────────────────────────────────────
:: STEP 6 - Create required IPC files
:: ─────────────────────────────────────────
echo [STEP 6] Creating IPC text files...
echo.

if not exist "fall_status.txt"       echo NONE > fall_status.txt
if not exist "accident_trigger.txt"  echo.     > accident_trigger.txt
if not exist "rear_warning.txt"      echo.     > rear_warning.txt
if not exist "hotspot_warning.txt"   echo.     > hotspot_warning.txt
if not exist "gps_log.txt"           echo.     > gps_log.txt
if not exist "latest_event.txt"      echo.     > latest_event.txt

echo   fall_status.txt      : OK
echo   accident_trigger.txt : OK
echo   rear_warning.txt     : OK
echo   hotspot_warning.txt  : OK
echo   gps_log.txt          : OK
echo   latest_event.txt     : OK

echo.

:: ─────────────────────────────────────────
:: STEP 7 - Delete old hotspot cache
:: ─────────────────────────────────────────
echo [STEP 7] Clearing old hotspot cache...
if exist "hotspot_cache.json" (
    del "hotspot_cache.json"
    echo   hotspot_cache.json deleted - will regenerate on first run
) else (
    echo   No cache found - OK
)

echo.

:: ─────────────────────────────────────────
:: STEP 8 - CARLA check
:: ─────────────────────────────────────────
echo [STEP 8] CARLA Setup Reminder...
echo.
echo   CARLA is NOT auto-installed (it is a large simulator).
echo   You must manually:
echo.
echo   1. Download CARLA 0.9.10 from:
echo      https://github.com/carla-simulator/carla/releases/tag/0.9.10
echo      File: CARLA_0.9.10.zip (WindowsNoEditor version)
echo.
echo   2. Extract to a folder, example: C:\CARLA_0.9.10\
echo.
echo   3. Open Merging_module_3.py and update line 21:
echo      sys.path.append(
echo        r"C:\CARLA_0.9.10\WindowsNoEditor\PythonAPI\carla\dist\carla-0.9.10-py3.7-win-amd64.egg"
echo      )
echo.
echo   4. Also update FALL_FILE path on line 57 to match
echo      your project folder location.
echo.

:: ─────────────────────────────────────────
:: STEP 9 - .env reminder
:: ─────────────────────────────────────────
echo [STEP 9] Hardware Configuration Reminder...
echo.
echo   Open .env file and update these values for your machine:
echo.
echo   ARDUINO_PORT = Check Device Manager ^> Ports ^> Arduino COM port
echo   ESP32_PORT   = Check Device Manager ^> Ports ^> ESP32 COM port
echo   ESP32_IP     = Check ESP32-CAM IP on your hotspot network
echo.

:: ─────────────────────────────────────────
:: DONE
:: ─────────────────────────────────────────
echo =============================================================
echo   INSTALLATION COMPLETE
echo =============================================================
echo.
echo   Next Steps:
echo   1. Install CARLA 0.9.10 manually (see Step 8 above)
echo   2. Update hardcoded paths in Merging_module_3.py
echo   3. Update COM ports and ESP32 IP in .env
echo   4. Run the project:
echo.
echo      Terminal 1: cd CARLA folder ^&^& CarlaUE4.exe
echo      Terminal 2: python Merging_module_3.py
echo      Terminal 3: python Rear_Location.py
echo      Terminal 4: python hotspot_detector.py  (optional)
echo.
echo   For evaluation metrics only (no hardware needed):
echo      python evaluation\thesis_evaluation.py
echo.
echo =============================================================
echo.
pause
