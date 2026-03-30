# import serial
# import time

# # Configuration
# SERIAL_PORT = 'COM3'           # Change to your actual ESP8266/NodeMCU COM port
# BAUD_RATE = 9600                # Match your NodeMCU baud rate
# OUTPUT_FILE = 'fall_status.txt' # File that CARLA will read

# # Stability filter settings
# last_state = 'NONE'
# state_count = 0
# STABILITY_THRESHOLD = 7         # Number of consistent readings before accepting

# def parse_fall_data(line):
#     """Extract fall direction from serial line (expects format like FALL:left or FALL:right or FALL:NONE)"""
#     if line.startswith('FALL:'):
#         try:
#             direction = line.split(':', 1)[1].strip().upper()
#             if direction in ['LEFT', 'RIGHT', 'NONE']:
#                 return direction
#         except:
#             pass
#     return None

# def update_file(state):
#     """Write state to file (LEFT / RIGHT / NONE)"""
#     try:
#         with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
#             f.write(state)
#         print(f"[{time.strftime('%H:%M:%S')}] Wrote to file: {state}")
#     except Exception as e:
#         print(f"File write error: {e}")

# def main():
#     global last_state, state_count
    
#     print(f"Starting fall detector...")
#     print(f"Listening on {SERIAL_PORT} at {BAUD_RATE} baud...")
#     print(f"Will write stable states to: {OUTPUT_FILE}")
    
#     try:
#         ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1.5)
#         print(f"Connected successfully to {SERIAL_PORT}")
        
#         # Start with NONE
#         update_file('NONE')
#         time.sleep(1)  # Give CARLA time to start reading if already running
        
#         while True:
#             try:
#                 line = ser.readline().decode('utf-8', errors='ignore').strip()
#                 if line:
#                     state = parse_fall_data(line)
#                     if state:
#                         if state == last_state:
#                             state_count += 1
#                             if state_count >= STABILITY_THRESHOLD:
#                                 update_file(state)
#                                 # Reset count after writing to avoid spamming
#                                 state_count = 0
#                         else:
#                             last_state = state
#                             state_count = 1
#                             print(f"New potential state: {state} (waiting for stability)")
                            
#             except UnicodeDecodeError:
#                 continue
#             except Exception as e:
#                 print(f"Read error: {e}")
#                 time.sleep(1)  # avoid tight loop on error
                
#     except serial.SerialException as e:
#         print(f"Cannot open serial port: {e}")
#         print("Check: 1. Correct COM port? 2. Device connected? 3. Baud rate matches?")
#     except KeyboardInterrupt:
#         print("\nStopping fall detector...")
#     finally:
#         if 'ser' in locals() and ser.is_open:
#             ser.close()
#         print("Serial port closed.")

# if __name__ == "__main__":
#     main()
import serial
import time
from datetime import datetime

# Configuration
SERIAL_PORT = 'COM20'           # Change to your actual ESP8266/NodeMCU COM port
BAUD_RATE = 9600                # Match your NodeMCU baud rate
OUTPUT_FILE = r'd:\CEG-MCA\Semester-4\Final-Year-Project\Module-4-Emergency-Alert\Live_location\fall_status.txt'

# Stability filter settings - REDUCED for faster response to small tilts
STABILITY_THRESHOLD = 3         # Reduced for faster tilt detection
DEBOUNCE_TIME = 0.1            # Minimum time between state changes (seconds)

# State tracking
last_state = 'NONE'
state_count = 0
last_change_time = 0

def parse_fall_data(line):
    """
    Extract fall direction from serial line
    Expects format: FALL:left or FALL:right or FALL:NONE
    """
    if line.startswith('FALL:'):
        try:
            direction = line.split(':', 1)[1].strip().upper()
            if direction in ['LEFT', 'RIGHT', 'NONE']:
                return direction
        except:
            pass
    return None

def update_file(state):
    """Write state to file for CARLA to read"""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(state)
        # Fixed timestamp - use datetime for milliseconds
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] ✓ State Updated: {state}")
    except Exception as e:
        print(f"❌ File write error: {e}")

def main():
    global last_state, state_count, last_change_time
    
    print("="*60)
    print("FALL DETECTION SYSTEM - Enhanced Tilt Sensitivity")
    print("="*60)
    print(f"Serial Port      : {SERIAL_PORT}")
    print(f"Baud Rate        : {BAUD_RATE}")
    print(f"Output File      : {OUTPUT_FILE}")
    print(f"Stability Count  : {STABILITY_THRESHOLD} readings")
    print(f"Debounce Time    : {DEBOUNCE_TIME}s")
    print("="*60)
    
    try:
        # Open serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1.0)
        print(f"✓ Connected to {SERIAL_PORT}\n")
        
        # Initialize with NONE state
        update_file('NONE')
        last_change_time = time.time()
        time.sleep(0.5)
        
        print("Monitoring tilt sensor... (Press Ctrl+C to stop)\n")
        
        while True:
            try:
                # Read line from serial
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line:
                        state = parse_fall_data(line)
                        
                        if state:
                            current_time = time.time()
                            
                            # Check if this is the same state
                            if state == last_state:
                                state_count += 1
                                
                                # If we've reached stability threshold and debounce time passed
                                if (state_count >= STABILITY_THRESHOLD and 
                                    current_time - last_change_time >= DEBOUNCE_TIME):
                                    update_file(state)
                                    last_change_time = current_time
                                    state_count = 0  # Reset after update
                                    
                            else:
                                # New state detected
                                timestamp = time.strftime('%H:%M:%S')
                                print(f"[{timestamp}] → Detecting: {state} (count: 1/{STABILITY_THRESHOLD})")
                                last_state = state
                                state_count = 1
                
                # Small delay to prevent CPU spinning
                time.sleep(0.01)
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"❌ Read error: {e}")
                time.sleep(0.5)
                
    except serial.SerialException as e:
        print(f"\n❌ Cannot open serial port: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if COM port is correct (Device Manager → Ports)")
        print("  2. Verify device is connected via USB")
        print("  3. Ensure baud rate matches NodeMCU code (9600)")
        print("  4. Close any other programs using this port (Arduino IDE, etc.)")
        
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("Stopping fall detector...")
        print("="*60)
        
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("✓ Serial port closed")

if __name__ == "__main__":
    main()