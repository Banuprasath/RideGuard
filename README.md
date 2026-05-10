<div align="center">

# 🏍️ RideGuard
### Motorcycle Accident Detection & Emergency Alert System

![Python](https://img.shields.io/badge/Python-3.7-blue?style=for-the-badge&logo=python)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple?style=for-the-badge)
![CARLA](https://img.shields.io/badge/CARLA-0.9.10-orange?style=for-the-badge)
![Telegram](https://img.shields.io/badge/Telegram-Bot-2CA5E0?style=for-the-badge&logo=telegram)
![Arduino](https://img.shields.io/badge/Arduino-IoT-00979D?style=for-the-badge&logo=arduino)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Final Year Project — MCA Semester 4**

*A real-time motorcycle accident detection system that combines computer vision, IoT sensors, machine learning, and automated emergency alerts to improve rider safety.*

[Features](#features) • [Architecture](#architecture) • [Modules](#modules) • [Installation](#installation) • [Usage](#usage) • [Evaluation](#evaluation) • [Tech Stack](#tech-stack)

</div>

---

## Overview

RideGuard is an integrated motorcycle safety system that detects accidents in real-time using multiple sensor inputs and immediately notifies emergency contacts via Telegram with GPS location and photographic evidence.

The system is simulated using the **CARLA 0.9.10** autonomous driving simulator and validated with real IoT hardware including Arduino, MPU6050, HC-SR04 ultrasonic sensor, Neo-6M GPS, and ESP32-CAM.

---

## Features

- **Helmet Detection** — YOLOv8 detects helmet usage every 5 seconds via webcam. Restricts speed to 30 km/h if no helmet detected
- **Tilt/Fall Detection** — MPU6050 gyroscope detects motorcycle tilt beyond 10 degrees and triggers fall animation in CARLA
- **Rear Collision Detection** — HC-SR04 ultrasonic sensor detects rear vehicle proximity. Triggers accident after 3 consecutive readings within 2cm
- **Accident Hotspot Warning** — DBSCAN clustering on 99 Chennai GPS accident records identifies 6 hotspot zones. Warns rider in real-time when within 2km
- **Emergency Alert** — Sends Telegram message with rider details, live GPS pin, and ESP32-CAM evidence photos within 20 seconds of accident

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RIDEGUARD SYSTEM                        │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   MODULE 1   │   MODULE 2   │   MODULE 3   │   MODULE 4     │
│   Helmet     │    Tilt      │    Rear      │   Hotspot      │
│  Detection   │  Detection   │  Collision   │  Detection     │
│  (YOLOv8)   │  (MPU6050)   │ (Ultrasonic) │   (DBSCAN)     │
└──────┬───────┴──────┬───────┴──────┬───────┴───────┬────────┘
       │              │              │               │
       └──────────────┴──────────────┴───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   FILE-BASED IPC  │
                    │  (Shared .txt     │
                    │   files between   │
                    │    processes)     │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────▼──────┐ ┌──────▼──────┐ ┌─────▼──────────┐
    │  CARLA 0.9.10  │ │  MODULE 5   │ │   HUD DISPLAY  │
    │  Simulation    │ │  Emergency  │ │  (Pygame)      │
    │  Fall Animation│ │  Alert      │ │                │
    └────────────────┘ │  (Telegram) │ └────────────────┘
                       └─────────────┘
```

---

## Modules

### Module 1 — Helmet Detection (YOLOv8)

Detects whether the rider is wearing a helmet using a custom-trained YOLOv8 model via laptop webcam.

- Model: `best.pt` (custom trained, 2 classes)
- Classes: `With Helmet` / `Without Helmet`
- Confidence threshold: `0.50`
- Check interval: every `5 seconds`
- Speed enforcement: `80% throttle` with helmet, `35% throttle` without

| Metric | Value |
|---|---|
| Accuracy | 90.00% |
| Precision | 88.46% |
| Recall | 92.00% |
| F1-Score | 0.9020 |

### Module 2 — Tilt Detection (MPU6050)

MPU6050 gyroscope sensor measures motorcycle tilt angle. When tilt exceeds 10 degrees, it writes LEFT or RIGHT to a shared file which CARLA reads to trigger a 3-stage fall animation.

- Tilt threshold: `10 degrees`
- Check interval: `5 seconds`
- Secondary verification: Sobel edge + image moment analysis on ESP32-CAM images
- MPU6050 takes priority over camera analysis

### Module 3 — Rear Collision Detection (HC-SR04 + ESP32-CAM)

HC-SR04 ultrasonic sensor monitors rear vehicle distance. Uses a 3-reading debounce buffer to prevent false triggers.

- Danger zone: `<= 2cm` (3 consecutive readings)
- Warning zone: `2cm to 6cm`
- On trigger: writes ACCIDENT to IPC file, sends CAPTURE command to ESP32-CAM
- ESP32-CAM captures 5 images saved to SD card

| Zone | Distance | Action |
|---|---|---|
| Safe | > 6cm | No action |
| Warning | 2–6cm | HUD warning |
| Danger | <= 2cm (x3) | Accident trigger |

### Module 4 — Accident Hotspot Detection (DBSCAN)

DBSCAN clustering on 99 GPS accident records from Chennai identifies 6 accident-prone zones. Background thread checks rider GPS every 60 seconds and warns if within 2km of any hotspot.

- Algorithm: DBSCAN (Density-Based Spatial Clustering)
- Dataset: 99 GPS records (Chennai)
- eps: `0.5km / 6371 = 0.0000785 radians`
- min_samples: `5`
- metric: `haversine`
- Warning radius: `2.0 km`

**Detected Hotspot Zones:**

| # | Area | Accidents |
|---|---|---|
| 1 | Koyambedu Junction | 18 |
| 2 | Madhya Kailash (OMR) | 19 |
| 3 | Kathipara Junction | 19 |
| 4 | Poonamallee High Road | 18 |
| 5 | Anna Salai (Gemini) | 18 |
| 6 | Tambaram Bypass | 7 |

| Clustering Metric | Value |
|---|---|
| Silhouette Score | 0.9879 |
| Davies-Bouldin Index | 0.0165 |
| Calinski-Harabasz | 395534.21 |

### Module 5 — Emergency Alert System (Telegram)

On any accident trigger, collects GPS location, ESP32-CAM images, and rider details. Sends Telegram alert within 18–21 seconds.

| Content | MPU Fall | Rear Collision |
|---|---|---|
| Text message | Yes | Yes |
| Live GPS pin | Yes | Yes |
| Evidence images | No | Yes (img_1 + img_5) |

---

## IPC Architecture

All modules communicate through shared text files (File-based IPC):

| File | Writer | Reader | Content |
|---|---|---|---|
| `fall_status.txt` | MPU6050/Arduino | Merging_module_3.py | LEFT / RIGHT / NONE |
| `accident_trigger.txt` | Rear_Location.py | Merging_module_3.py | ACCIDENT |
| `rear_warning.txt` | Rear_Location.py | Merging_module_3.py | WARNING |
| `hotspot_warning.txt` | hotspot_detector.py | Merging_module_3.py | WARNING\|count\|dist |
| `gps_log.txt` | Rear_Location.py | emergency_alert.py | timestamp,lat,lng,sats |
| `telegram_status.txt` | emergency_alert.py | Merging_module_3.py | SENT |

---

## Installation

### Prerequisites

- Python 3.7 (strict requirement for CARLA compatibility)
- CARLA 0.9.10 Simulator
- Arduino IDE (for hardware code upload)

### Step 1 — Clone the repository

```bash
git clone https://github.com/Banuprasath/RideGuard.git
cd RideGuard
```

### Step 2 — Run the installer

```bash
install.bat
```

Or manually install dependencies:

```bash
pip install -r requirements.txt
```

### Step 3 — Configure environment

```bash
copy .env.example .env
```

Edit `.env` with your values:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ARDUINO_PORT=COM16
ESP32_PORT=COM3
ESP32_IP=192.168.137.X
```

### Step 4 — Install CARLA 0.9.10

Download from: https://github.com/carla-simulator/carla/releases/tag/0.9.10

Extract to `C:\CARLA_0.9.10\` then update the path in `Merging_module_3.py` line 21:

```python
sys.path.append(
    r"C:\CARLA_0.9.10\WindowsNoEditor\PythonAPI\carla\dist\carla-0.9.10-py3.7-win-amd64.egg"
)
```

### Step 5 — YOLOv8 model

The trained `best.pt` model is included in the repository root. No separate download needed.

If you want to retrain the model:

```bash
python train_helmet.py
```

---

## Usage

Open 4 terminals and run in order:

```bash
# Terminal 1 — Start CARLA Server
cd C:\CARLA_0.9.10\WindowsNoEditor
CarlaUE4.exe

# Terminal 2 — Main System
cd RideGuard
python Merging_module_3.py

# Terminal 3 — Hardware Bridge
python Rear_Location.py

# Terminal 4 — Hotspot Monitor
python hotspot_detector.py
```

### Controls (in CARLA window)

| Key | Action |
|---|---|
| W / S | Throttle / Brake |
| A / D | Steer Left / Right |
| Arrow Left / Right | Simulate fall direction |
| 1 | Toggle helmet detection test |
| 2 | Trigger rear collision sequence |
| BACKSPACE | Reset after accident |
| C | Switch camera view |
| ESC | Quit |

---

## Evaluation

Run evaluation metrics (no hardware required):

```bash
python evaluation\thesis_evaluation.py
```

Generates 3 output images in `evaluation/` folder:

| File | Description |
|---|---|
| `helmet_confusion_matrix.png` | YOLOv8 confusion matrix |
| `dbscan_hotspot_clusters.png` | DBSCAN cluster scatter plot |
| `dbscan_unsupervised_evaluation.png` | Silhouette plot + cluster size chart |

### Overall System Metrics

| Module | Metric | Value |
|---|---|---|
| Helmet Detection | Accuracy | 90.00% |
| Helmet Detection | F1-Score | 0.9020 |
| Tilt Detection | Success Rate | 92% |
| Rear Collision | Detection Accuracy | 95% |
| Emergency Alert | End-to-end Time | 18–21 seconds |
| DBSCAN Hotspot | Silhouette Score | 0.9879 |

---

## Project Structure

```
RideGuard/
├── Merging_module_3.py        # Main CARLA + Helmet + Tilt module
├── Rear_Location.py           # Hardware bridge (Arduino + GPS + ESP32)
├── emergency_alert.py         # Telegram alert + evidence logging
├── hotspot_detector.py        # DBSCAN hotspot detection + monitor
├── compare_hotspot_algorithms.py  # ML algorithm comparison
├── test_gps.py                # Neo-6M GPS test utility
├── train_helmet.py            # YOLOv8 training script
├── best.pt                    # Trained YOLOv8 helmet detection model
├── yolov8n.pt                 # YOLOv8 nano base model
├── accidents.csv              # 99 Chennai GPS accident records
├── requirements.txt           # Python dependencies
├── install.bat                # Auto installer for Windows
├── SETUP_GUIDE.txt            # Manual setup instructions
├── .env.example               # Environment config template
├── evaluation/                # Thesis evaluation scripts + charts
├── Neo-6M_Connections/        # Arduino GPS + Ultrasonic code
├── Testing_Dataset/           # Test CSVs for evaluation
├── Thesis/                    # Final year thesis report + viva PDF
├── utils/                     # Debug and utility scripts
└── tests/                     # Integration test scripts
```

---

## Tech Stack

| Category | Technology |
|---|---|
| Simulation | CARLA 0.9.10 |
| Computer Vision | YOLOv8 (Ultralytics) |
| Machine Learning | DBSCAN (scikit-learn) |
| Hardware | Arduino Uno, MPU6050, HC-SR04, Neo-6M GPS, ESP32-CAM |
| Rendering | Pygame |
| Image Processing | OpenCV |
| Alert System | Telegram Bot API |
| Language | Python 3.7 |
| Data | Pandas, NumPy |
| Visualization | Matplotlib |
| Serial Comm | PySerial |

---

## Hardware Connections

### Arduino (COM16, 9600 baud)
- HC-SR04: TRIG → D9, ECHO → D10
- Neo-6M GPS: TX → D2, RX → D3

### ESP32-CAM (COM3, 115200 baud)
- Receives CAPTURE command via serial
- Serves images via HTTP at `http://ESP32_IP/image`

---

## Thesis & Documentation

The full project thesis and viva presentation are available in the `Thesis/` folder:

| File | Description |
|---|---|
| `Thesis/Final_year_report_Banu_Prasath_crt (1).pdf` | Complete project thesis report |
| `Thesis/Banu-Prasath_S_Final_Viva.pdf` | Final viva presentation slides |

---

## Author

**Banuprasath S**
MCA Final Year — Semester 4
GitHub: [@Banuprasath](https://github.com/Banuprasath)
Repository: [RideGuard](https://github.com/Banuprasath/RideGuard)

---

## License

This project is licensed under the MIT License.

---

<div align="center">
Built with dedication for Final Year Project — MCA Semester 4
</div>
