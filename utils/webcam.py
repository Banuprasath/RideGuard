import serial
import time
import cv2
import numpy as np
import os
from datetime import datetime
from collections import deque

# ================= SETTINGS =================
ARDUINO_PORT = "COM16"
BAUD_RATE = 9600

DIST_THRESHOLD = 5         # cm
CONFIRM_COUNT = 3
PHOTO_COUNT = 10
PHOTO_DELAY = 0.5          # seconds between photos
TILT_THRESHOLD = 15        # degrees
CAMERA_WARMUP = 1.5        # seconds for camera initialization
# ===========================================


class AccidentDetector:
    def __init__(self, port, baud_rate):
        self.ser = serial.Serial(port, baud_rate, timeout=1)
        time.sleep(2)
        self.distance_buffer = deque(maxlen=CONFIRM_COUNT)
        self.busy = False
        print("📡 Accident Detection System initialized")

    def get_tilt_angle(self, image_path):
        """Calculate tilt angle using Hough Line Transform"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                print(f"⚠️ Failed to load image: {image_path}")
                return 0

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Enhanced edge detection with blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

            # Detect lines
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)
            
            if lines is None or len(lines) < 5:
                return 0

            angles = []
            for line in lines[:30]:  # Consider more lines for better average
                rho, theta = line[0]
                angle = (theta - np.pi / 2) * 180 / np.pi
                
                # Filter out near-horizontal/vertical lines (likely noise)
                if -45 < angle < 45:
                    angles.append(angle)

            if not angles:
                return 0

            # Use median instead of mean for robustness
            return float(np.median(angles))

        except Exception as e:
            print(f"❌ Tilt calculation error: {e}")
            return 0

    def capture_images(self, folder):
        """Capture multiple images with error handling"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Camera initialization failed")
            return False

        # Camera warm-up
        print("📷 Warming up camera...")
        time.sleep(CAMERA_WARMUP)
        
        # Discard first few frames
        for _ in range(5):
            cap.read()

        captured = 0
        for i in range(1, PHOTO_COUNT + 1):
            ret, frame = cap.read()
            
            if not ret:
                print(f"❌ Failed to capture image {i}")
                continue

            img_path = os.path.join(folder, f"img_{i}.jpg")
            success = cv2.imwrite(img_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            if success:
                print(f"📸 Saved: img_{i}.jpg")
                captured += 1
            else:
                print(f"❌ Failed to save: img_{i}.jpg")

            time.sleep(PHOTO_DELAY)

        cap.release()
        cv2.destroyAllWindows()
        
        return captured >= PHOTO_COUNT // 2  # Success if at least 50% captured

    def analyze_accident(self, folder):
        """Analyze tilt change and determine accident"""
        first_img = os.path.join(folder, "img_1.jpg")
        last_img = os.path.join(folder, f"img_{PHOTO_COUNT}.jpg")

        # Check if files exist
        if not (os.path.exists(first_img) and os.path.exists(last_img)):
            print("❌ Image files missing for analysis")
            return False, 0, 0

        angle_first = self.get_tilt_angle(first_img)
        angle_last = self.get_tilt_angle(last_img)

        print(f"📐 Tilt first: {angle_first:.2f}° | Tilt last: {angle_last:.2f}°")
        
        tilt_change = abs(angle_last - angle_first)
        is_accident = tilt_change > TILT_THRESHOLD

        # Save detailed results
        result_path = os.path.join(folder, "result.txt")
        with open(result_path, "w") as f:
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"First Image Tilt: {angle_first:.2f}°\n")
            f.write(f"Last Image Tilt: {angle_last:.2f}°\n")
            f.write(f"Tilt Change: {tilt_change:.2f}°\n")
            f.write(f"Threshold: {TILT_THRESHOLD}°\n")
            f.write(f"\nResult: {'ACCIDENT DETECTED' if is_accident else 'NO ACCIDENT'}\n")

        return is_accident, angle_first, angle_last

    def process_detection(self):
        """Main detection workflow"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder = f"accident_{timestamp}"
        os.makedirs(folder, exist_ok=True)

        print(f"\n🚨 Threshold reached → Capturing images to '{folder}'")

        # Capture images
        if not self.capture_images(folder):
            print("❌ Image capture failed")
            self.busy = False
            return

        # Analyze
        is_accident, angle_first, angle_last = self.analyze_accident(folder)

        if is_accident:
            print("🚨 ACCIDENT DETECTED - Vehicle fell down!")
        else:
            print("✅ NO ACCIDENT - Normal detection")

        print(f"📁 Results saved in '{folder}'\n")
        self.busy = False

    def run(self):
        """Main loop"""
        print("🔍 Monitoring distance sensor...\n")

        while True:
            try:
                line = self.ser.readline().decode(errors="ignore").strip()

                if line.startswith("DIST:"):
                    try:
                        distance = int(line.replace("DIST:", ""))
                    except ValueError:
                        continue

                    print(f"📏 Distance: {distance} cm", end="\r")

                    if not self.busy:
                        # Use buffer for stable detection
                        self.distance_buffer.append(distance <= DIST_THRESHOLD)
                        
                        if len(self.distance_buffer) == CONFIRM_COUNT and all(self.distance_buffer):
                            self.busy = True
                            self.distance_buffer.clear()
                            self.process_detection()

                time.sleep(0.1)

            except KeyboardInterrupt:
                print("\n\n🛑 System stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(1)

        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.ser.close()
        cv2.destroyAllWindows()
        print("✅ Cleanup complete")


# ================= MAIN =================
if __name__ == "__main__":
    detector = AccidentDetector(ARDUINO_PORT, BAUD_RATE)
    detector.run()