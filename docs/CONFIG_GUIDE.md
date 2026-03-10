# Configuration Guide

## Centralized Configuration (.env)

All hardware ports, IP addresses, and detection thresholds are now managed in a single `.env` file.

### Location
```
Module-3-RearRecord/iot-python/.env
```

### Configuration Parameters

#### Telegram Notifications
```
TELEGRAM_BOT_TOKEN=8786560050:AAGgWkj-LZHTrJz0jVdXTdBLF8gzsTlSAHE
TELEGRAM_CHAT_ID=1947794898
PHONE_NUMBER=+917373940409
```

#### User Information
```
USER_NAME=Rider Name              # Rider's name for alerts
VEHICLE_NUMBER=TN00XX0000         # Vehicle registration number
```

#### Hardware Configuration
```
ESP32_IP=192.168.137.30          # ESP32-CAM IP address
ESP32_STREAM_URL=http://192.168.137.63:81/stream
ARDUINO_PORT=COM16               # Ultrasonic sensor Arduino port
ESP32_PORT=COM3                  # ESP32-CAM serial port
```

#### Detection Thresholds
```
DIST_THRESHOLD=4                 # Rear collision distance (cm)
WARNING_THRESHOLD=7              # Proximity warning distance (cm)
TILT_THRESHOLD=15                # Tilt detection angle (degrees)
CONFIRM_COUNT=3                  # Consecutive readings to confirm
TRIGGER_COOLDOWN=15              # Cooldown between triggers (seconds)
```

## How to Update Configuration

### Change User Information
```
USER_NAME=John Doe
VEHICLE_NUMBER=TN01AB1234
```

### Change ESP32 IP Address
```
ESP32_IP=192.168.137.XX
```

### Change COM Ports
```
ARDUINO_PORT=COMXX
ESP32_PORT=COMXX
```

### Adjust Detection Sensitivity
```
DIST_THRESHOLD=5        # Increase for less sensitive
WARNING_THRESHOLD=10    # Increase warning zone
TILT_THRESHOLD=20       # Increase for less sensitive tilt detection
```

## Files Using .env Configuration

1. **gpt-intergration.py** - Hardware integration bridge
   - Reads: ARDUINO_PORT, ESP32_PORT, ESP32_IP
   - Reads: DIST_THRESHOLD, WARNING_THRESHOLD, TILT_THRESHOLD
   - Reads: CONFIRM_COUNT, TRIGGER_COOLDOWN

2. **emergency_alert.py** - Evidence logging & notifications
   - Reads: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
   - Reads: ESP32_IP, PHONE_NUMBER

3. **Merging_module_3.py** - CARLA simulation
   - Uses emergency_alert.py (indirect .env usage)

## Benefits

✅ **Single Source of Truth** - All configuration in one file  
✅ **Easy Updates** - Change IP/ports without editing code  
✅ **No Code Changes** - Update .env and restart scripts  
✅ **Version Control Safe** - Can gitignore .env for security  
✅ **Quick Debugging** - Adjust thresholds without code edits  

## Restart Required

After changing `.env`, restart these scripts:
- `gpt-intergration.py`
- `Merging_module_3.py` (if running)

No code changes needed! 🎉
