import serial
import time
import cv2
import numpy as np
import os
import requests
import threading
from datetime import datetime
from collections import deque

# ================= LOAD CONFIGURATION FROM .ENV =================
def load_env_var(var_name, default_value):
    """Load variable from .env file"""
    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and line.startswith(f'{var_name}='):
                    value = line.split('=', 1)[1].strip()
                    # Try to convert to int if possible
                    try:
                        return int(value)
                    except ValueError:
                        return value
    except Exception as e:
        print(f"[DEBUG][ENV] Error reading {var_name}: {e}")
    return default_value

# Hardware Configuration
ARDUINO_PORT = load_env_var('ARDUINO_PORT', 'COM16')
ESP32_PORT = load_env_var('ESP32_PORT', 'COM3')
ESP32_IP = load_env_var('ESP32_IP', '192.168.137.30')

# Detection Thresholds
DIST_THRESHOLD = load_env_var('DIST_THRESHOLD', 4)
WARNING_THRESHOLD = load_env_var('WARNING_THRESHOLD', 7)
TILT_THRESHOLD = load_env_var('TILT_THRESHOLD', 15)
CONFIRM_COUNT = load_env_var('CONFIRM_COUNT', 3)
TRIGGER_COOLDOWN = load_env_var('TRIGGER_COOLDOWN', 15)

# Serial Settings
ARDUINO_BAUD = 9600
ESP32_BAUD = 115200

# File paths
ACCIDENT_TRIGGER_FILE = "accident_trigger.txt"
WARNING_TRIGGER_FILE = "rear_warning.txt"
GPS_LOG_FILE = "gps_log.txt"
GPS_LOG_INTERVAL = load_env_var('GPS_LOG_INTERVAL', 15)

print(f"[CONFIG] Loaded from .env: ARDUINO={ARDUINO_PORT}, ESP32={ESP32_PORT}, IP={ESP32_IP}")
print(f"[CONFIG] Thresholds: DIST={DIST_THRESHOLD}cm, WARN={WARNING_THRESHOLD}cm, TILT={TILT_THRESHOLD}°")
# ===============================================


# ---------- Load image from ESP32 ----------
def load_image_from_esp32(path):
    """Download image from ESP32 web server"""
    try:
        url = f"http://{ESP32_IP}/image?file={path}"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        img_array = np.frombuffer(r.content, np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


# ---------- Tilt calculation using orientation ----------
def get_orientation_angle(img):
    """Calculate image orientation using edge analysis"""
    if img is None:
        return 0.0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    
    
    angles = np.arctan2(sobely, sobelx) * 180 / np.pi
    # angle = tan−1(Y/X)
    
    
    hist, bins = np.histogram(angles, bins=180, range=(-90, 90))
    
    
    dominant_angle = bins[np.argmax(hist)]
    
    return float(dominant_angle)


# ---------- Simple rotation detection ----------
def detect_rotation(img1, img2):
    """Detect if camera rotated between two images"""
    if img1 is None or img2 is None:
        return 0.0
    
    # Convert to grayscale
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # Resize for faster processing
    gray1 = cv2.resize(gray1, (320, 240))
    gray2 = cv2.resize(gray2, (320, 240))
    
    # Calculate image moments to detect orientation
    moments1 = cv2.moments(gray1)
    moments2 = cv2.moments(gray2)
    
    # Calculate orientation from moments
    if moments1['mu20'] != moments1['mu02']:
        angle1 = 0.5 * np.arctan2(2 * moments1['mu11'], moments1['mu20'] - moments1['mu02']) * 180 / np.pi
    else:
        angle1 = 0
    
    if moments2['mu20'] != moments2['mu02']:
        angle2 = 0.5 * np.arctan2(2 * moments2['mu11'], moments2['mu20'] - moments2['mu02']) * 180 / np.pi
    else:
        angle2 = 0
    
    rotation_diff = abs(angle2 - angle1)
    
    return rotation_diff, angle1, angle2


# ---------- Get latest ESP32 event ----------
def get_latest_event():
    """Get latest event folder name from ESP32"""
    try:
        r = requests.get(f"http://{ESP32_IP}/latest", timeout=5)
        if r.status_code == 200:
            return r.text.strip()
    except Exception as e:
        print(f"Error getting latest event: {e}")
    return None


# ---------- Analyze tilt ----------
def analyze_tilt():
    """Download all 5 images from ESP32 and perform comprehensive tilt analysis"""
    event = get_latest_event()
    if not event:
        print("❌ No event folder found on ESP32")
        return False
    
    print(f"📁 Analyzing event: {event}")
    
    # Download all 5 images
    images = []
    for i in range(1, 6):
        img = load_image_from_esp32(f"/ACCIDENT/{event}/img_{i}.jpg")
        if img is not None:
            images.append((i, img))
            print(f"[DEBUG] Image {i} downloaded: {img.shape}")
        else:
            print(f"[DEBUG] Image {i} failed to download")
    
    if len(images) < 2:
        print("❌ Not enough images for analysis")
        return False
    
    print(f"\n📊 Analyzing {len(images)} images for tilt detection...")
    
    # Compare consecutive images for progressive tilt
    tilt_results = []
    for i in range(len(images) - 1):
        idx1, img1 = images[i]
        idx2, img2 = images[i + 1]
        
        # Method 1: Edge-based
        angle1 = get_orientation_angle(img1)
        angle2 = get_orientation_angle(img2)
        edge_diff = abs(angle2 - angle1)
        
        # Method 2: Moment-based
        moment_diff, m_angle1, m_angle2 = detect_rotation(img1, img2)
        
        max_diff = max(edge_diff, moment_diff)
        tilt_results.append({
            'pair': f"{idx1}-{idx2}",
            'edge_diff': edge_diff,
            'moment_diff': moment_diff,
            'max_diff': max_diff
        })
        
        print(f"  📐 Image {idx1}→{idx2}: Edge={edge_diff:.2f}°, Moment={moment_diff:.2f}°, Max={max_diff:.2f}°")
    
    # Calculate overall tilt (first to last image)
    first_img = images[0][1]
    last_img = images[-1][1]
    
    angle_first = get_orientation_angle(first_img)
    angle_last = get_orientation_angle(last_img)
    overall_edge = abs(angle_last - angle_first)
    
    overall_moment, _, _ = detect_rotation(first_img, last_img)
    overall_tilt = max(overall_edge, overall_moment)
    
    # Find maximum progressive tilt
    max_progressive = max([r['max_diff'] for r in tilt_results])
    
    print(f"\n📐 Overall Tilt (img 1→{len(images)}): {overall_tilt:.2f}°")
    print(f"📐 Max Progressive Tilt: {max_progressive:.2f}°")
   # print(f"📐 Threshold: {TILT_THRESHOLD}°")
    
    # Decision: tilt detected if either overall or progressive exceeds threshold
    tilt_detected = (overall_tilt > TILT_THRESHOLD) or (max_progressive > TILT_THRESHOLD)
    
    result = "TILT DETECTED" if tilt_detected else "NO TILT"
    print(f"\n🧠 Camera Analysis Result: {result}")
    
    return tilt_detected


# ================= GPS LOGGING =================
def gps_logger_thread(arduino, gps_log_file, interval):
    """Background thread to log GPS every 15 seconds"""
    last_gps = None
    while True:
        try:
            if last_gps:
                with open(gps_log_file, "w") as f:
                    f.write(f"{last_gps['timestamp']},{last_gps['lat']},{last_gps['lng']},{last_gps['sats']}")
        except:
            pass
        time.sleep(interval)

# ================= MAIN SYSTEM =================
class AccidentSystem:
    def __init__(self):
        self.arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)

        self.esp32 = serial.Serial(
            ESP32_PORT, ESP32_BAUD,
            timeout=1, dsrdtr=False, rtscts=False
        )

        self.esp32.dtr = False
        self.esp32.rts = False

        time.sleep(4)

        self.buffer = deque(maxlen=CONFIRM_COUNT)
        self.last_trigger = 0
        self.busy = False
        self.latest_event_name = None
        self.last_gps = None
        self.last_gps_log_time = 0

        print("📡 Accident Detection System READY")
        print(f"🌐 ESP32-CAM IP: {ESP32_IP}")
        print(f"📍 GPS logging every {GPS_LOG_INTERVAL}s")

    def trigger_capture(self):
        print("\n📤 Sending CAPTURE to ESP32-CAM")
        self.esp32.write(b"CAPTURE\n")
        self.esp32.flush()

    def run(self):
        print("🔍 Monitoring distance + GPS...\n")

        while True:
            try:
                line = self.arduino.readline().decode(errors="ignore").strip()

                if line.startswith("GPS:"):
                    parts = line.replace("GPS:", "").split(",")
                    if len(parts) == 4:
                        self.last_gps = {
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'lat': float(parts[0]),
                            'lng': float(parts[1]),
                            'sats': int(parts[2])
                        }
                        now = time.time()
                        if now - self.last_gps_log_time >= GPS_LOG_INTERVAL:
                            with open(GPS_LOG_FILE, "w") as f:
                                f.write(f"{self.last_gps['timestamp']},{self.last_gps['lat']},{self.last_gps['lng']},{self.last_gps['sats']}")
                            self.last_gps_log_time = now
                            print(f"\n📍 GPS logged: {self.last_gps['lat']:.6f},{self.last_gps['lng']:.6f} ({self.last_gps['sats']} sats)")

                elif line.startswith("DIST:"):
                    distance = int(line.replace("DIST:", ""))
                    print(f"📏 Distance: {distance} cm", end="\r")

                    now = time.time()

                    if not self.busy:
                        # Check for warning zone (9cm > distance > 5cm)
                        if distance > DIST_THRESHOLD and distance <= WARNING_THRESHOLD:
                            # Write warning signal
                            try:
                                with open(WARNING_TRIGGER_FILE, "w") as f:
                                    f.write("WARNING")
                                print(f"\n[WARN][REAR] Rear vehicle very close (warning zone) - {distance}cm")
                            except Exception as e:
                                print(f"⚠️ Could not write warning: {e}")
                        else:
                            # Clear warning if distance is safe
                            try:
                                with open(WARNING_TRIGGER_FILE, "w") as f:
                                    f.write("")
                            except:
                                pass
                        
                        self.buffer.append(distance <= DIST_THRESHOLD)

                        if (
                            len(self.buffer) == CONFIRM_COUNT
                            and all(self.buffer)
                            and (now - self.last_trigger) > TRIGGER_COOLDOWN
                        ):
                            self.busy = True
                            self.buffer.clear()
                            self.last_trigger = now

                            print("\n🚨 Distance threshold confirmed")
                            
                            # IMMEDIATELY trigger CARLA accident
                            print("⚡ TRIGGERING CARLA ACCIDENT NOW!")
                            try:
                                with open(ACCIDENT_TRIGGER_FILE, "w") as f:
                                    f.write("ACCIDENT")
                                print("✅ CARLA accident triggered!")
                            except Exception as e:
                                print(f"⚠️ Could not trigger CARLA: {e}")
                            
                            # Then capture images for analysis (background)
                            self.trigger_capture()

                            # Wait for ESP32 to save images
                            time.sleep(5)
                            
                            # Wait and poll for fall direction (MPU sensor updates slowly)
                            print("\n⏳ Waiting for MPU sensor data to update...")
                            fall_direction = "NONE"
                            for attempt in range(10):  # Poll for 5 seconds (10 x 0.5s)
                                try:
                                    with open(r"d:\CEG-MCA\Semester-4\Final-Year-Project\Module-3-RearRecord\iot-python\fall_status.txt", "r") as f:
                                        current_status = f.read().strip().upper()
                                        if current_status in ["LEFT", "RIGHT"]:
                                            fall_direction = current_status
                                            print(f"📐 Fall detected: {fall_direction} (attempt {attempt + 1})")
                                            break
                                        elif attempt == 0:
                                            print(f"📐 Current status: {current_status} (waiting for update...)")
                                except Exception as e:
                                    print(f"⚠️ Could not read fall_status.txt: {e}")
                                time.sleep(0.5)
                            
                            print(f"📐 Final fall direction: {fall_direction}")

                            # Store latest event name for evidence logging
                            self.latest_event_name = get_latest_event()
                            print(f"[DEBUG][EVENT] Latest ESP32 event: {self.latest_event_name}")
                            
                            # Write event name to shared file for CARLA
                            try:
                                with open("latest_event.txt", "w") as f:
                                    f.write(self.latest_event_name if self.latest_event_name else "")
                            except:
                                pass

                            # Analyze images from ESP32
                            camera_tilt_detected = analyze_tilt()
                            
                            # Final result combining MPU sensor and camera analysis
                            if fall_direction in ["LEFT", "RIGHT"]:
                                print(f"\n🚨🚨 FINAL RESULT: ACCIDENT CONFIRMED! 🚨🚨")
                                print(f"   ↳ Rear collision + {fall_direction} fall detected (MPU)")
                                if camera_tilt_detected:
                                    print(f"   ↳ Camera analysis: TILT CONFIRMED")
                                else:
                                    print(f"   ↳ Camera analysis: No significant tilt (MPU takes priority)")
                            elif fall_direction == "NONE":
                                if camera_tilt_detected:
                                    print(f"\n⚠️ FINAL RESULT: CONFLICTING DATA")
                                    print(f"   ↳ MPU: No fall | Camera: Tilt detected")
                                    print(f"   ↳ Decision: REAR COLLISION ONLY (MPU takes priority)")
                                else:
                                    print(f"\n⚠️ FINAL RESULT: REAR COLLISION ONLY (No fall detected)")
                                    print(f"   ↳ Vehicle close but rider upright")
                                    print(f"   ↳ Both MPU and Camera confirm: NO TILT")
                            else:
                                print(f"\n⚠️ FINAL RESULT: Minor hit")
                                print(f"   ↳ fall_status: {fall_direction}")

                            self.busy = False

                time.sleep(0.1)

            except KeyboardInterrupt:
                print("\n🛑 Stopped by user")
                break

        self.arduino.close()
        self.esp32.close()


# ================= RUN =================
if __name__ == "__main__":
    system = AccidentSystem()
    system.run()
