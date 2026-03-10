# import serial
# import time
# from datetime import datetime

# # Two separate serial connections
# arduino = serial.Serial("COM16", 9600, timeout=1)  # Ultrasonic
# esp32cam = serial.Serial("COM11", 115200, timeout=1)  # ESP32-CAM

# time.sleep(2)

# print("📡 Dual-port system initialized")

# while True:
#     try:
#         # Read distance from Arduino
#         line = arduino.readline().decode(errors="ignore").strip()
        
#         if line.startswith("DIST:"):
#             distance = int(line.replace("DIST:", ""))
#             print(f"📏 Distance: {distance} cm", end="\r")
            
#             if distance <= 5:
#                 print("\n🚨 Threshold reached - Sending CAPTURE to ESP32-CAM")
#                 esp32cam.write(b"CAPTURE\n")
#                 esp32cam.flush()
                
#                 # Wait for ESP32-CAM response
#                 time.sleep(8)  # Give it time to capture all photos
                
#                 while esp32cam.in_waiting:
#                     response = esp32cam.readline().decode(errors="ignore").strip()
#                     print(f"📷 ESP32: {response}")
        
#         time.sleep(0.1)
        
#     except KeyboardInterrupt:
#         print("\n🛑 Stopped")
#         break

# arduino.close()
# esp32cam.close()





import serial
import time

ser = serial.Serial(
    port="COM11",
    baudrate=115200,
    timeout=1,
    dsrdtr=False,
    rtscts=False
)

# 🔴 CRITICAL: disable auto-reset
ser.dtr = False
ser.rts = False

time.sleep(4)          # wait for ESP32-CAM to fully boot

ser.write(b"CAPTURE\n")
ser.flush()

print("Sent CAPTURE")

time.sleep(1)          # keep port open briefly
ser.close()
