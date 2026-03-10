# File Structure Reference

## Status Files Location (ROOT FOLDER)

All status files used for inter-process communication MUST be in the root `iot-python` folder:

```
iot-python/
├── fall_status.txt          ← MPU6050 tilt status (LEFT/RIGHT/NONE)
├── accident_trigger.txt     ← Accident trigger signal (ACCIDENT/NONE)
├── rear_warning.txt         ← Rear warning signal (WARNING/NONE)
├── latest_event.txt         ← ESP32 event folder name (event_XXXXX)
└── trigger.txt              ← Legacy trigger file
```

## Why Root Folder?

1. **CARLA Integration**: `Merging_module_3.py` runs from root and reads these files
2. **Hardware Bridge**: `gpt-intergration.py` runs from root and writes these files
3. **Relative Paths**: All scripts use relative paths from root directory

## Scripts That Write Status Files

### 1. `utils/serial_to_file.py`
- **Writes**: `fall_status.txt`
- **Path**: `../fall_status.txt` (parent directory)
- **Content**: LEFT, RIGHT, or NONE
- **Source**: MPU6050 sensor via Serial (COM20)

### 2. `gpt-intergration.py`
- **Writes**: `accident_trigger.txt`, `rear_warning.txt`, `latest_event.txt`
- **Path**: Direct (runs from root)
- **Content**: 
  - `accident_trigger.txt`: ACCIDENT or empty
  - `rear_warning.txt`: WARNING or empty
  - `latest_event.txt`: event_XXXXX or empty
- **Source**: Arduino ultrasonic + ESP32-CAM

## Scripts That Read Status Files

### 1. `Merging_module_3.py`
- **Reads**: All status files
- **Path**: Direct (runs from root)
- **Purpose**: CARLA simulation integration

### 2. `emergency_alert.py`
- **Reads**: `latest_event.txt`
- **Path**: Direct (called from root)
- **Purpose**: Evidence logging with ESP32 event ID

## Common Issues & Fixes

### Issue: Status files not updating
**Cause**: Script writing to wrong directory (e.g., `utils/fall_status.txt` instead of root)
**Fix**: Use `../fall_status.txt` when running from `utils/` folder

### Issue: CARLA not detecting accidents
**Cause**: Reading from wrong file location
**Fix**: Ensure all scripts run from `iot-python` root directory

### Issue: Duplicate status files
**Cause**: Scripts creating files in multiple locations
**Fix**: Delete duplicates, keep only root folder versions

## Running Scripts

### From Root Directory
```bash
cd iot-python
python Merging_module_3.py          # CARLA simulation
python gpt-intergration.py          # Hardware bridge
```

### From Utils Directory
```bash
cd iot-python/utils
python serial_to_file.py            # MPU6050 reader (writes to ../fall_status.txt)
```

## File Content Examples

### fall_status.txt
```
LEFT
```
or
```
RIGHT
```
or
```
NONE
```

### accident_trigger.txt
```
ACCIDENT
```
or (empty file)

### rear_warning.txt
```
WARNING
```
or (empty file)

### latest_event.txt
```
event_36785
```
or (empty file)

## Folder Structure

```
iot-python/
├── docs/                    ← Documentation
├── evaluation/              ← Evaluation scripts & results
├── logs/                    ← Log files
├── records/                 ← Evidence folders (timestamped)
├── Testing_Dataset/         ← CSV test data
├── tests/                   ← Test scripts
├── utils/                   ← Utility scripts
│   ├── serial_to_file.py   ← MPU6050 reader
│   ├── ultrasonic.py       ← Ultrasonic test
│   └── webcam.py           ← Webcam test
├── .env                     ← Configuration file
├── Merging_module_3.py     ← Main CARLA script
├── gpt-intergration.py     ← Hardware bridge
├── emergency_alert.py      ← Evidence logging
├── fall_status.txt         ← Status file (ROOT)
├── accident_trigger.txt    ← Status file (ROOT)
├── rear_warning.txt        ← Status file (ROOT)
└── latest_event.txt        ← Status file (ROOT)
```

## Important Notes

1. **Never move status files** from root folder
2. **Always use relative paths** when writing from subdirectories
3. **Run main scripts from root** directory
4. **Check file paths** if communication fails
5. **Delete duplicate files** in subdirectories

---

*Last Updated: March 2026*
