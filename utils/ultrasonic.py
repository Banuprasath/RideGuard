# ipc_bridge.py
import serial
import time

ARDUINO_PORT = 'COM16'
ESP32_PORT = 'COM17'
ARDUINO_BAUD = 9600
ESP32_BAUD = 115200

STATE_IDLE = 0
STATE_CAPTURING = 1
STATE_COOLDOWN = 2

state = STATE_IDLE
consecutive_close = 0
cooldown_end = 0
trigger_time = 0

try:
    arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=0.2, 
                           dsrdtr=False, rtscts=False)
    esp32 = serial.Serial(ESP32_PORT, ESP32_BAUD, timeout=0.2,
                         dsrdtr=False, rtscts=False)
    
    time.sleep(2)
    
    # Clear any startup messages from ESP32
    while esp32.in_waiting > 0:
        line = esp32.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print(f"ESP32 startup: {line}")
    
    print("System ready.\n")
    
    while True:
        # Read from Arduino
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("Distance:"):
                try:
                    dist_str = line.replace("Distance:", "").replace("cm", "")
                    distance = int(dist_str)
                    print(f"Distance: {distance} cm")
                    
                    if state == STATE_IDLE:
                        if distance <= 10:
                            consecutive_close += 1
                            if consecutive_close >= 2:
                                print("\n>>> Sending RECORD to ESP32-CAM...")
                                esp32.write(b"RECORD\n")
                                esp32.flush()
                                state = STATE_CAPTURING
                                consecutive_close = 0
                                trigger_time = time.time()
                        else:
                            consecutive_close = 0
                            
                except ValueError:
                    pass
        
        # Read from ESP32-CAM
        if esp32.in_waiting > 0:
            line = esp32.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"[ESP32] {line}")
                
                if line.startswith("DONE") and state == STATE_CAPTURING:
                    print(">>> Capture finished. Entering 12s cooldown...\n")
                    state = STATE_COOLDOWN
                    cooldown_end = time.time() + 12
        
        # Timeout safety: if capturing for >10 seconds without DONE, reset
        if state == STATE_CAPTURING:
            if time.time() - trigger_time > 10:
                print("!!! Capture timeout - forcing cooldown\n")
                state = STATE_COOLDOWN
                cooldown_end = time.time() + 12
        
        # Handle cooldown
        if state == STATE_COOLDOWN:
            if time.time() >= cooldown_end:
                print(">>> Cooldown complete. Back to IDLE.\n")
                state = STATE_IDLE
                consecutive_close = 0
        
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nShutting down...")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'arduino' in locals():
        arduino.close()
    if 'esp32' in locals():
        esp32.close()
    print("Serial ports closed.")