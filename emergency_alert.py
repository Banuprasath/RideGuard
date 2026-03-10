import os
import requests
import threading
import time
from datetime import datetime

# ================= CONFIGURATION =================
def load_env_var(var_name, default_value):
    """Load variable from .env file"""
    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and line.startswith(f'{var_name}='):
                    value = line.split('=', 1)[1].strip()
                    return value
    except FileNotFoundError:
        print(f"[DEBUG][ENV] .env file not found, using default for {var_name}")
    except Exception as e:
        print(f"[DEBUG][ENV] Error reading .env: {e}")
    return default_value

def get_esp32_ip_from_gpt_integration():
    """Read ESP32_IP from .env file (single source of truth)"""
    return load_env_var('ESP32_IP', '192.168.137.30')

TELEGRAM_BOT_TOKEN = load_env_var('TELEGRAM_BOT_TOKEN', '8786560050:AAGgWkj-LZHTrJz0jVdXTdBLF8gzsTlSAHE')
TELEGRAM_CHAT_ID = load_env_var('TELEGRAM_CHAT_ID', '1947794898')
ESP32_IP = get_esp32_ip_from_gpt_integration()
USER_NAME = load_env_var('USER_NAME', 'Rider Name')
VEHICLE_NUMBER = load_env_var('VEHICLE_NUMBER', 'TN00XX0000')

RECORDS_DIR = "records"
ESP32_ACCIDENT_PATH = "/ACCIDENT"

# ================= LOCATION CAPTURE =================
def get_location(carla_transform=None):
    # ALWAYS try GPS first (priority)
    try:
        with open("gps_log.txt", "r") as f:
            data = f.read().strip().split(",")
            if len(data) == 4 and float(data[1]) != 0.0 and float(data[2]) != 0.0:
                # Check GPS age
                gps_time = datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S")
                gps_age_seconds = (datetime.now() - gps_time).total_seconds()
                
                # If GPS is fresh (< 2 minutes), it's LIVE
                if gps_age_seconds < 120:
                    print(f"[DEBUG][LOCATION] ✅ GPS LIVE: {data[1]},{data[2]} ({gps_age_seconds:.0f}s old)")
                    return {
                        'lat': float(data[1]),
                        'lng': float(data[2]),
                        'satellites': int(data[3]),
                        'source': 'GPS_LIVE'
                    }
                else:
                    print(f"[DEBUG][LOCATION] ⚠️ GPS Location: {data[1]},{data[2]} ({gps_age_seconds:.0f}s old)")
                    return {
                        'lat': float(data[1]),
                        'lng': float(data[2]),
                        'satellites': int(data[3]),
                        'source': 'GPS_Liveee'
                    }
    except Exception as e:
        print(f"[DEBUG][LOCATION] GPS not available: {e}")
    
    # Fallback to CARLA if GPS unavailable
    if carla_transform:
        location = carla_transform.location
        rotation = carla_transform.rotation
        print(f"[DEBUG][LOCATION] ⚠️ Using CARLA fallback: X={location.x:.2f}, Y={location.y:.2f}")
        return {
            'x': round(location.x, 2),
            'y': round(location.y, 2),
            'z': round(location.z, 2),
            'yaw': round(rotation.yaw, 2),
            'source': 'CARLA_FALLBACK'
        }
    else:
        print("[DEBUG][LOCATION] No location available")
        return {'x': 0.0, 'y': 0.0, 'z': 0.0, 'yaw': 0.0, 'source': 'UNKNOWN'}

# ================= EVIDENCE STORAGE =================
def create_evidence_folder():
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base_folder = os.path.join(RECORDS_DIR, timestamp)
        images_folder = os.path.join(base_folder, "images")
        os.makedirs(images_folder, exist_ok=True)
        print(f"[DEBUG][STORAGE] Evidence folder created: {base_folder}")
        return base_folder, images_folder
    except Exception as e:
        print(f"[ERROR][STORAGE] Failed to create evidence folder: {e}")
        return None, None

def copy_images_from_esp32(images_folder, event_name):
    if not images_folder or not event_name:
        print("[DEBUG][IMAGES] Invalid folder or event name")
        return 0, []
    
    copied_count = 0
    telegram_image_paths = []  # Only images 1 and 5 for Telegram
    
    try:
        print(f"[DEBUG][IMAGES] Downloading all 5 images from ESP32 event: {event_name}")
        print(f"[DEBUG][IMAGES] Using ESP32_IP: {ESP32_IP}")
        
        # Download all 5 images for local analysis
        for i in range(1, 6):
            try:
                url = f"http://{ESP32_IP}/image?file={ESP32_ACCIDENT_PATH}/{event_name}/img_{i}.jpg"
                response = requests.get(url, timeout=1)
                
                if response.status_code == 200:
                    img_path = os.path.join(images_folder, f"img_{i}.jpg")
                    with open(img_path, 'wb') as f:
                        f.write(response.content)
                    copied_count += 1
                    
                    # Only add images 1 and 5 for Telegram
                    if i in [1, 5]:
                        telegram_image_paths.append(img_path)
                    
                    print(f"[DEBUG][IMAGES] ✓ Saved: img_{i}.jpg")
            except Exception as e:
                print(f"[DEBUG][IMAGES] ✗ Failed img_{i}.jpg: {str(e)[:50]}")
        
        print(f"[DEBUG][IMAGES] Total images copied: {copied_count}/5")
        print(f"[DEBUG][IMAGES] Images for Telegram: {len(telegram_image_paths)}/2")
        return copied_count, telegram_image_paths
    except Exception as e:
        print(f"[ERROR][IMAGES] Failed to copy images: {e}")
        return 0, []

def create_metadata(base_folder, trigger_source, location_data, esp32_event_name=None):
    try:
        metadata_path = os.path.join(base_folder, "metadata.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(metadata_path, 'w') as f:
            f.write("=== ACCIDENT EVIDENCE METADATA ===\n\n")
            f.write(f"Rider Name: {USER_NAME}\n")
            f.write(f"Vehicle Number: {VEHICLE_NUMBER}\n")
            if esp32_event_name:
                f.write(f"ESP32 Event ID: {esp32_event_name}\n")
            f.write(f"\nTimestamp: {timestamp}\n")
            f.write(f"Trigger Source: {trigger_source}\n")
            f.write(f"\nLocation Data:\n")
            f.write(f"  Source: {location_data.get('source', 'UNKNOWN')}\n")
            if 'lat' in location_data:
                f.write(f"  Latitude: {location_data.get('lat', 0.0)}\n")
                f.write(f"  Longitude: {location_data.get('lng', 0.0)}\n")
                f.write(f"  Satellites: {location_data.get('satellites', 0)}\n")
            else:
                f.write(f"  X: {location_data.get('x', 0.0)}\n")
                f.write(f"  Y: {location_data.get('y', 0.0)}\n")
                f.write(f"  Z: {location_data.get('z', 0.0)}\n")
                f.write(f"  Yaw: {location_data.get('yaw', 0.0)}\n")
        
        print(f"[DEBUG][METADATA] Metadata file created: {metadata_path}")
    except Exception as e:
        print(f"[ERROR][METADATA] Failed to create metadata: {e}")

# ================= TELEGRAM NOTIFICATION =================
def send_telegram_alert_with_images(trigger_source, location_data, base_folder, image_paths, esp32_event_name=None):
    try:
        print("[DEBUG][TELEGRAM] Waiting 10 seconds before sending alert...")
        time.sleep(8)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"🚨 ACCIDENT DETECTED 🚨\n\n"
        message += f"👤 Rider: {USER_NAME}\n"
        message += f"🏍️ Vehicle: {VEHICLE_NUMBER}\n\n"
        message += f"⏰ Time: {timestamp}\n"
        
        if 'lat' in location_data:
            message += f"📍 GPS Location ({location_data.get('source', 'GPS')}):\n"
            message += f"   Lat: {location_data.get('lat', 0.0):.6f}\n"
            message += f"   Lng: {location_data.get('lng', 0.0):.6f}\n"
            message += f"   Satellites: {location_data.get('satellites', 0)}\n"
        else:
            message += f"📍 Location (CARLA):\n"
            message += f"   X: {location_data.get('x', 0.0)}\n"
            message += f"   Y: {location_data.get('y', 0.0)}\n"
            message += f"   Z: {location_data.get('z', 0.0)}\n"
        
        message += f"🔔 Trigger: {trigger_source}\n"
        message += f"📁 Evidence: {os.path.basename(base_folder)}\n"
        if esp32_event_name:
            message += f"📹 ESP32 Event: {esp32_event_name}\n"
        message += f"📷 Images: {len(image_paths)}/2"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
        
        print(f"[DEBUG][TELEGRAM] Sending alert to chat ID: {TELEGRAM_CHAT_ID}")
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("[DEBUG][TELEGRAM] ✅ Message sent!")
            # Write success notification to file for CARLA
            try:
                with open("telegram_status.txt", "w") as f:
                    f.write("SENT")
            except:
                pass
        else:
            print(f"[ERROR][TELEGRAM] Message failed - Status: {response.status_code}")
            print(f"[ERROR][TELEGRAM] Response: {response.text}")
        
        # Send live location if GPS available
        if 'lat' in location_data:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendLocation"
                payload = {
                    'chat_id': TELEGRAM_CHAT_ID,
                    'latitude': location_data['lat'],
                    'longitude': location_data['lng']
                }
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    print("[DEBUG][TELEGRAM] ✅ Live location sent!")
            except Exception as e:
                print(f"[ERROR][TELEGRAM] Live location failed: {e}")
        
        if image_paths:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            for img_path in image_paths:
                try:
                    with open(img_path, 'rb') as f:
                        files = {'photo': f}
                        data = {'chat_id': TELEGRAM_CHAT_ID}
                        requests.post(url, files=files, data=data, timeout=10)
                    print(f"[DEBUG][TELEGRAM] ✅ Image sent: {os.path.basename(img_path)}")
                except Exception as e:
                    print(f"[ERROR][TELEGRAM] Image failed: {e}")
    except Exception as e:
        print(f"[ERROR][TELEGRAM] Exception: {e}")

def send_alert_async(trigger_source, location_data, base_folder, image_paths, esp32_event_name=None):
    thread = threading.Thread(
        target=send_telegram_alert_with_images,
        args=(trigger_source, location_data, base_folder, image_paths, esp32_event_name),
        daemon=True
    )
    thread.start()
    print("[DEBUG][TELEGRAM] Alert thread started (will send after 30s)")

# ================= MAIN PIPELINE =================
def log_accident_evidence(carla_transform, trigger_source, esp32_event_name=None):
    print("\n" + "="*60)
    print("[EVIDENCE] Starting accident evidence logging pipeline")
    print("="*60)
    
    location_data = get_location(carla_transform)
    base_folder, images_folder = create_evidence_folder()
    
    if not base_folder:
        print("[ERROR][EVIDENCE] Failed to create evidence folder, aborting")
        return None
    
    copied_count = 0
    image_paths = []
    if esp32_event_name:
        copied_count, image_paths = copy_images_from_esp32(images_folder, esp32_event_name)
        print(f"[EVIDENCE] Images copied: {copied_count}/5 (Telegram: {len(image_paths)}/2)")
    else:
        print("[DEBUG][EVIDENCE] No ESP32 event name provided, skipping image copy")
    
    create_metadata(base_folder, trigger_source, location_data, esp32_event_name)
    
    # Always send alert, even if no images downloaded
    send_alert_async(trigger_source, location_data, base_folder, image_paths, esp32_event_name)
    
    if copied_count > 0:
        print(f"[EVIDENCE] ✅ Alert scheduled (15s delay) with {len(image_paths)} image(s)")
    else:
        print("[EVIDENCE] ⚠️ No images downloaded - alert sent WITHOUT images")
    
    print("="*60)
    print(f"[EVIDENCE] ✅ Evidence logging completed: {base_folder}")
    print("="*60 + "\n")
    
    return base_folder
