# User Information Feature - Implementation Summary

## What Changed

Added **USER_NAME** and **VEHICLE_NUMBER** to the emergency alert system.

---

## Configuration (.env)

```env
# User Information
USER_NAME=Rider Name              # Change to actual rider name
VEHICLE_NUMBER=TN00XX0000         # Change to actual vehicle number
```

---

## Telegram Alert Format (NEW)

```
🚨 ACCIDENT DETECTED 🚨

👤 Rider: Rider Name
🏍️ Vehicle: TN00XX0000

⏰ Time: 2026-02-27 09:16:34
📍 Location:
   X: 78.43
   Y: -27.47
   Z: 1.57
🔔 Trigger: REAR_COLLISION
📁 Evidence: 2026-02-27_09-16-34
📷 Images: 2/2
```

**Plus 2 accident images attached**

---

## Metadata File (metadata.txt) - NEW FORMAT

```
=== ACCIDENT EVIDENCE METADATA ===

Rider Name: Rider Name
Vehicle Number: TN00XX0000

Timestamp: 2026-02-27 09:16:34
Trigger Source: REAR_COLLISION

Location Data:
  Source: CARLA
  X: 78.43
  Y: -27.47
  Z: 1.57
  Yaw: 180.0
```

---

## How to Update

### Step 1: Edit .env file
```bash
# Open: Module-3-RearRecord/iot-python/.env

USER_NAME=John Doe
VEHICLE_NUMBER=TN01AB1234
```

### Step 2: Restart the system
- No code changes needed
- Just restart `Merging_module_3.py`

---

## Files Modified

1. **`.env`** - Added USER_NAME and VEHICLE_NUMBER
2. **`emergency_alert.py`** - Loads user info and includes in alerts
3. **`CONFIG_GUIDE.md`** - Updated documentation

---

## Benefits

✅ **Identifies the rider** in emergency alerts  
✅ **Vehicle tracking** for multiple bikes  
✅ **Easy to update** - just edit .env file  
✅ **Professional alerts** with complete information  
✅ **Metadata logging** for evidence records  

---

## Example Use Cases

### Single Rider
```
USER_NAME=Rajesh Kumar
VEHICLE_NUMBER=TN09AB1234
```

### Fleet Management (Multiple Bikes)
Each bike has its own .env configuration:

**Bike 1:**
```
USER_NAME=Driver A
VEHICLE_NUMBER=TN01XX1111
```

**Bike 2:**
```
USER_NAME=Driver B
VEHICLE_NUMBER=TN01XX2222
```

---

## Testing

1. Update `.env` with your details
2. Trigger an accident (press `2` key in CARLA)
3. Wait 30 seconds
4. Check Telegram - should show your name and vehicle number

---

**Implementation Complete!** 🎉
