import serial
import time
from datetime import datetime

# Configuration
ARDUINO_PORT = 'COM16'
BAUD_RATE = 9600

print("="*60)
print("NEO-6M GPS MODULE TEST")
print("="*60)
print(f"Port: {ARDUINO_PORT}")
print(f"Baud Rate: {BAUD_RATE}")
print("\nWaiting for GPS data...\n")
print("Note: GPS needs clear sky view. May take 30-60 seconds to lock.")
print("Press Ctrl+C to stop\n")
print("="*60 + "\n")

try:
    # Connect to Arduino
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    
    gps_count = 0
    dist_count = 0
    last_gps = None
    
    while True:
        try:
            line = arduino.readline().decode(errors="ignore").strip()
            
            if line.startswith("GPS:"):
                gps_count += 1
                parts = line.replace("GPS:", "").split(",")
                
                if len(parts) == 4:
                    lat = float(parts[0])
                    lng = float(parts[1])
                    sats = int(parts[2])
                    speed = float(parts[3])
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    print(f"\n[{timestamp}] GPS DATA #{gps_count}")
                    print(f"  Latitude:   {lat:.6f}")
                    print(f"  Longitude:  {lng:.6f}")
                    print(f"  Satellites: {sats}")
                    print(f"  Speed:      {speed:.2f} km/h")
                    
                    if sats == 0:
                        print("  Status:     ⚠️ NO SATELLITE LOCK (Move to open area)")
                    elif sats < 4:
                        print("  Status:     ⚠️ WEAK SIGNAL (Need 4+ satellites)")
                    else:
                        print("  Status:     ✅ GOOD SIGNAL")
                    
                    last_gps = {"lat": lat, "lng": lng, "sats": sats, "time": timestamp}
            
            elif line.startswith("DIST:"):
                dist_count += 1
                distance = int(line.replace("DIST:", ""))
                print(f"[DIST] {distance} cm", end="\r")
            
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"Error parsing line: {e}")
            continue
    
except KeyboardInterrupt:
    print("\n\n" + "="*60)
    print("TEST STOPPED BY USER")
    print("="*60)
    print(f"\nStatistics:")
    print(f"  GPS readings received: {gps_count}")
    print(f"  Distance readings: {dist_count}")
    
    if last_gps:
        print(f"\nLast GPS Location:")
        print(f"  Lat: {last_gps['lat']:.6f}")
        print(f"  Lng: {last_gps['lng']:.6f}")
        print(f"  Satellites: {last_gps['sats']}")
        print(f"  Time: {last_gps['time']}")
        print(f"\n  Google Maps: https://www.google.com/maps?q={last_gps['lat']},{last_gps['lng']}")
    else:
        print("\n⚠️ No GPS data received!")
        print("Troubleshooting:")
        print("  1. Check GPS module wiring (TX→D2, RX→D3, VCC→5V, GND→GND)")
        print("  2. Move to outdoor location with clear sky view")
        print("  3. Wait 1-2 minutes for satellite lock")
        print("  4. Check Arduino code is uploaded correctly")
    
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print(f"  1. Check if Arduino is connected to {ARDUINO_PORT}")
    print("  2. Close Arduino IDE Serial Monitor if open")
    print("  3. Check if correct Arduino code is uploaded")

finally:
    try:
        arduino.close()
        print("\nSerial port closed.")
    except:
        pass
