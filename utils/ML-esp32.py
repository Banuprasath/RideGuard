import serial
import time
import cv2
import numpy as np
import requests
from collections import deque

# ================= CONFIG =================
ARDUINO_PORT = "COM16"
ESP32_PORT   = "COM11"
ESP32_IP     = "192.168.137.235"   # ESP32-CAM IP

ARDUINO_BAUD = 9600
ESP32_BAUD   = 115200

DIST_THRESHOLD = 5        # cm
CONFIRM_COUNT = 3
TRIGGER_COOLDOWN = 15     # seconds
# =========================================


# ---------- Load image from ESP32 ----------
def load_image_from_esp32(path):
    try:
        url = f"http://{ESP32_IP}/image?file={path}"
        r = requests.get(url, timeout=5)

        if r.status_code != 200:
            return None

        img_array = np.frombuffer(r.content, np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except:
        return None


# ---------- DETECT ORIENTATION CHANGE (Fall/Tilt) ----------
def detect_orientation_change(img1, img2):
    """
    Detects if camera orientation changed significantly (vertical <-> horizontal)
    Using edge direction analysis
    """
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # Detect edges
    edges1 = cv2.Canny(gray1, 50, 150)
    edges2 = cv2.Canny(gray2, 50, 150)
    
    # Calculate edge orientation histograms
    sobelx1 = cv2.Sobel(gray1, cv2.CV_64F, 1, 0, ksize=3)
    sobely1 = cv2.Sobel(gray1, cv2.CV_64F, 0, 1, ksize=3)
    
    sobelx2 = cv2.Sobel(gray2, cv2.CV_64F, 1, 0, ksize=3)
    sobely2 = cv2.Sobel(gray2, cv2.CV_64F, 0, 1, ksize=3)
    
    # Calculate dominant orientation
    angle1 = np.arctan2(sobely1, sobelx1)
    angle2 = np.arctan2(sobely2, sobelx2)
    
    # Get histogram of orientations
    hist1, _ = np.histogram(angle1, bins=36, range=(-np.pi, np.pi))
    hist2, _ = np.histogram(angle2, bins=36, range=(-np.pi, np.pi))
    
    # Normalize histograms
    hist1 = hist1 / (np.sum(hist1) + 1e-7)
    hist2 = hist2 / (np.sum(hist2) + 1e-7)
    
    # Calculate histogram difference
    orientation_diff = np.sum(np.abs(hist1 - hist2))
    
    print(f"📐 Orientation change: {orientation_diff:.3f}")
    
    # If orientation changed significantly → Fall/Tilt detected
    if orientation_diff > 0.5:
        return True
    
    return False


# ---------- ENHANCED SHAKE DETECTION ----------
def detect_shake_accident(img1, img2):
    """
    Improved shake detection with multiple methods
    """
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Method 1: ORB Feature Matching
    orb = cv2.ORB_create(500)
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)

    motion_detected = False

    if des1 is not None and des2 is not None:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)

        if len(matches) >= 30:
            pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
            pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])

            motion = np.linalg.norm(pts2 - pts1, axis=1)

            avg_motion = np.mean(motion)
            max_motion = np.max(motion)

            print(f"🧪 Feature motion - Avg: {avg_motion:.2f} | Max: {max_motion:.2f}")

            # Increased threshold for more reliable detection
            if avg_motion > 35 or max_motion > 75:
                motion_detected = True

    # Method 2: Frame Difference (Blur detection)
    diff = cv2.absdiff(gray1, gray2)
    blur_score = np.mean(diff)
    
    print(f"🌫️  Frame difference (blur): {blur_score:.2f}")
    
    # High difference = significant motion/shake
    if blur_score > 40:
        motion_detected = True

    # Method 3: Structural Similarity
    # Resize for faster computation
    small1 = cv2.resize(gray1, (100, 100))
    small2 = cv2.resize(gray2, (100, 100))
    
    diff_small = cv2.absdiff(small1, small2)
    structural_diff = np.sum(diff_small) / (100 * 100)
    
    print(f"🏗️  Structural difference: {structural_diff:.2f}")
    
    if structural_diff > 35:
        motion_detected = True

    return motion_detected


# ---------- Analyze latest ESP32 event ----------
def analyze_latest_event():
    try:
        r = requests.get(f"http://{ESP32_IP}/latest", timeout=5)
        event = r.text.strip()
    except:
        print("❌ Failed to get latest event")
        return

    print(f"\n📁 Latest event: {event}")

    img1 = load_image_from_esp32(f"/ACCIDENT/{event}/img_1.jpg")
    img5 = load_image_from_esp32(f"/ACCIDENT/{event}/img_5.jpg")

    if img1 is None or img5 is None:
        print("❌ Failed to load images from ESP32")
        return

    print("\n🔍 Analyzing images...")
    print("=" * 50)

    # Check for orientation change (fall/tilt)
    orientation_changed = detect_orientation_change(img1, img5)
    
    # Check for shake/sudden movement
    shake_detected = detect_shake_accident(img1, img5)

    print("=" * 50)

    # ACCIDENT if either condition is met
    if orientation_changed or shake_detected:
        print("\n🚨🚨 ACCIDENT DETECTED 🚨🚨")
        if orientation_changed:
            print("   ↳ Reason: Orientation change (Fall/Tilt)")
        if shake_detected:
            print("   ↳ Reason: Sudden shake/movement")
    else:
        print("\n✅ NO ACCIDENT - System stable")


# ================= MAIN SYSTEM =================
class AccidentSystem:
    def __init__(self):
        self.arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)

        self.esp32 = serial.Serial(
            ESP32_PORT,
            ESP32_BAUD,
            timeout=1,
            dsrdtr=False,
            rtscts=False
        )

        # Prevent ESP32 reset
        self.esp32.dtr = False
        self.esp32.rts = False

        time.sleep(4)

        self.buffer = deque(maxlen=CONFIRM_COUNT)
        self.last_trigger = 0
        self.busy = False

        print("📡 Accident Detection System READY")
        print("🌐 ESP32 IP:", ESP32_IP)

    def trigger_capture(self):
        print("\n📤 Sending CAPTURE to ESP32-CAM")
        self.esp32.write(b"CAPTURE\n")
        self.esp32.flush()

    def run(self):
        print("🔍 Monitoring distance...\n")

        while True:
            try:
                line = self.arduino.readline().decode(errors="ignore").strip()

                if line.startswith("DIST:"):
                    distance = int(line.replace("DIST:", ""))
                    print(f"📏 Distance: {distance} cm", end="\r")

                    now = time.time()

                    if not self.busy:
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
                            self.trigger_capture()

                            # Wait for ESP32 to capture
                            time.sleep(8)

                            # Analyze images
                            analyze_latest_event()

                            self.busy = False

                time.sleep(0.1)

            except KeyboardInterrupt:
                print("\n🛑 System stopped by user")
                break

        self.arduino.close()
        self.esp32.close()


# ================= RUN =================
if __name__ == "__main__":
    system = AccidentSystem()
    system.run()