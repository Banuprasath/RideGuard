import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from datetime import datetime
import json
import os
import time
import threading
import math

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
                    try:
                        return float(value)
                    except ValueError:
                        return value
    except Exception as e:
        print(f"[HOTSPOT][ENV] Error reading {var_name}: {e}")
    return default_value

RISK_RADIUS = load_env_var('RISK_RADIUS', 2.0)  # km
ACCIDENT_THRESHOLD = load_env_var('ACCIDENT_THRESHOLD', 5)  # minimum accidents
HOTSPOT_CHECK_INTERVAL = load_env_var('HOTSPOT_CHECK_INTERVAL', 60)  # seconds (1 minute)
HOTSPOT_COOLDOWN = load_env_var('HOTSPOT_COOLDOWN', 300)  # 5 minutes

ACCIDENTS_CSV = "accidents.csv"
HOTSPOT_CACHE = "hotspot_cache.json"
HOTSPOT_WARNING_FILE = "hotspot_warning.txt"
GPS_LOG_FILE = "gps_log.txt"

print(f"[HOTSPOT][CONFIG] Risk Radius: {RISK_RADIUS} km")
print(f"[HOTSPOT][CONFIG] Accident Threshold: {int(ACCIDENT_THRESHOLD)}")
print(f"[HOTSPOT][CONFIG] Check Interval: {int(HOTSPOT_CHECK_INTERVAL)}s")

# ================= HAVERSINE DISTANCE =================
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in kilometers"""
    R = 6371  # Earth radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

# ================= HOTSPOT DETECTION =================
def detect_hotspots():
    """Use DBSCAN to detect accident-prone areas"""
    try:
        if not os.path.exists(ACCIDENTS_CSV):
            print(f"[HOTSPOT] No accident data found ({ACCIDENTS_CSV})")
            return []
        
        # Load accident data
        df = pd.read_csv(ACCIDENTS_CSV)
        
        if len(df) < ACCIDENT_THRESHOLD:
            print(f"[HOTSPOT] Not enough accidents ({len(df)}) for analysis")
            return []
        
        print(f"[HOTSPOT] Analyzing {len(df)} accidents...")
        
        # Extract coordinates
        coords = df[['latitude', 'longitude']].values
        
        # Convert km to degrees (approximate: 1 degree ≈ 111 km)
        eps_degrees = RISK_RADIUS / 111.0
        
        # Apply DBSCAN clustering
        dbscan = DBSCAN(eps=eps_degrees, min_samples=int(ACCIDENT_THRESHOLD), metric='haversine')
        
        # Convert to radians for haversine metric
        coords_rad = np.radians(coords)
        labels = dbscan.fit_predict(coords_rad)
        
        # Extract hotspots (cluster centroids)
        hotspots = []
        unique_labels = set(labels)
        
        for label in unique_labels:
            if label == -1:  # Noise points
                continue
            
            cluster_points = coords[labels == label]
            centroid_lat = cluster_points[:, 0].mean()
            centroid_lng = cluster_points[:, 1].mean()
            accident_count = len(cluster_points)
            
            hotspots.append({
                'lat': centroid_lat,
                'lng': centroid_lng,
                'count': accident_count,
                'radius': RISK_RADIUS
            })
        
        print(f"[HOTSPOT] ✅ Detected {len(hotspots)} accident-prone areas")
        
        # Cache results
        with open(HOTSPOT_CACHE, 'w') as f:
            json.dump({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'hotspots': hotspots
            }, f, indent=2)
        
        return hotspots
    
    except Exception as e:
        print(f"[HOTSPOT] ❌ Error detecting hotspots: {e}")
        return []

# ================= LOAD HOTSPOTS =================
def load_hotspots():
    """Load hotspots from cache or detect new ones"""
    try:
        if os.path.exists(HOTSPOT_CACHE):
            with open(HOTSPOT_CACHE, 'r') as f:
                data = json.load(f)
                print(f"[HOTSPOT] Loaded {len(data['hotspots'])} hotspots from cache")
                return data['hotspots']
    except:
        pass
    
    return detect_hotspots()

# ================= PROXIMITY CHECK =================
def check_proximity(current_lat, current_lng, hotspots):
    """Check if current location is near any hotspot"""
    for hotspot in hotspots:
        distance = haversine_distance(
            current_lat, current_lng,
            hotspot['lat'], hotspot['lng']
        )
        
        if distance <= hotspot['radius']:
            return True, hotspot, distance
    
    return False, None, None

# ================= REAL-TIME MONITOR =================
class HotspotMonitor:
    def __init__(self):
        self.hotspots = load_hotspots()
        self.last_warning_time = 0
        self.last_hotspot_id = None
        self.running = False
        
        print(f"[HOTSPOT] Monitor initialized with {len(self.hotspots)} hotspots")
    
    def get_current_gps(self):
        """Read current GPS from log file"""
        try:
            with open(GPS_LOG_FILE, 'r') as f:
                data = f.read().strip().split(',')
                if len(data) >= 3:
                    return float(data[1]), float(data[2])
        except:
            pass
        return None, None
    
    def check_and_warn(self):
        """Check current location and trigger warning if needed"""
        lat, lng = self.get_current_gps()
        
        if lat is None or lng is None:
            return
        
        in_hotspot, hotspot, distance = check_proximity(lat, lng, self.hotspots)
        
        if in_hotspot:
            current_time = time.time()
            hotspot_id = f"{hotspot['lat']:.4f},{hotspot['lng']:.4f}"
            
            # Check cooldown
            if (current_time - self.last_warning_time > HOTSPOT_COOLDOWN or 
                self.last_hotspot_id != hotspot_id):
                
                self.last_warning_time = current_time
                self.last_hotspot_id = hotspot_id
                
                # Write warning to file
                try:
                    with open(HOTSPOT_WARNING_FILE, 'w') as f:
                        f.write(f"WARNING|{hotspot['count']}|{distance:.2f}")
                    
                    print(f"\n[HOTSPOT] ⚠️ WARNING: Accident-prone area!")
                    print(f"[HOTSPOT]    Distance: {distance:.2f} km")
                    print(f"[HOTSPOT]    Accidents: {hotspot['count']}")
                    print(f"[HOTSPOT]    Location: {hotspot['lat']:.6f}, {hotspot['lng']:.6f}\n")
                except Exception as e:
                    print(f"[HOTSPOT] Error writing warning: {e}")
        else:
            # Clear warning
            try:
                with open(HOTSPOT_WARNING_FILE, 'w') as f:
                    f.write("")
            except:
                pass
    
    def start(self):
        """Start monitoring in background thread"""
        self.running = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
        print(f"[HOTSPOT] 🔍 Monitoring started (checking every {int(HOTSPOT_CHECK_INTERVAL)}s)")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                self.check_and_warn()
            except Exception as e:
                print(f"[HOTSPOT] Error in monitor loop: {e}")
            
            time.sleep(HOTSPOT_CHECK_INTERVAL)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        print("[HOTSPOT] Monitoring stopped")

# ================= MAIN =================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("ACCIDENT HOTSPOT DETECTION SYSTEM")
    print("="*60 + "\n")
    
    # Detect hotspots
    hotspots = detect_hotspots()
    
    if hotspots:
        print("\nDetected Hotspots:")
        for i, h in enumerate(hotspots, 1):
            print(f"  {i}. Lat: {h['lat']:.6f}, Lng: {h['lng']:.6f}")
            print(f"     Accidents: {h['count']}, Radius: {h['radius']} km")
        
        # Start monitoring
        monitor = HotspotMonitor()
        monitor.start()
        
        print("\n" + "="*60)
        print("Press Ctrl+C to stop monitoring")
        print("="*60 + "\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop()
            print("\n[HOTSPOT] Stopped by user")
    else:
        print("\n[HOTSPOT] No hotspots detected. Add more accident data to accidents.csv")
