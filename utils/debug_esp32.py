"""
ESP32-CAM Connection Debugger
Helps identify and fix ESP32 connection issues
"""

import requests
import socket
import subprocess
import time

print("="*70)
print("ESP32-CAM CONNECTION DEBUGGER".center(70))
print("="*70)

# Read current IP from .env
def read_env_ip():
    try:
        with open('../.env', 'r') as f:
            for line in f:
                if line.startswith('ESP32_IP='):
                    return line.split('=')[1].strip()
    except:
        pass
    return None

current_ip = read_env_ip()
print(f"\n[INFO] Current ESP32_IP in .env: {current_ip}")

# Step 1: Check if IP is reachable (ping)
print("\n" + "="*70)
print("STEP 1: PING TEST")
print("="*70)

if current_ip:
    print(f"\n[TEST] Pinging {current_ip}...")
    try:
        # Windows ping command
        result = subprocess.run(
            ['ping', '-n', '2', current_ip],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "Reply from" in result.stdout or "bytes=" in result.stdout:
            print(f"✅ SUCCESS: {current_ip} is reachable!")
        else:
            print(f"❌ FAILED: {current_ip} is not responding to ping")
            print("Possible reasons:")
            print("  1. ESP32 is not powered on")
            print("  2. ESP32 is not connected to WiFi")
            print("  3. Wrong IP address")
            print("  4. Firewall blocking ping")
    except Exception as e:
        print(f"❌ ERROR: {e}")

# Step 2: Test HTTP connection
print("\n" + "="*70)
print("STEP 2: HTTP CONNECTION TEST")
print("="*70)

if current_ip:
    print(f"\n[TEST] Testing HTTP connection to {current_ip}...")
    
    # Test root endpoint
    try:
        response = requests.get(f"http://{current_ip}/", timeout=3)
        print(f"✅ Root endpoint: Status {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"❌ Root endpoint: Connection timeout (ESP32 not responding)")
    except requests.exceptions.ConnectionError:
        print(f"❌ Root endpoint: Connection refused (ESP32 not running web server)")
    except Exception as e:
        print(f"❌ Root endpoint: {e}")
    
    # Test /latest endpoint
    try:
        response = requests.get(f"http://{current_ip}/latest", timeout=3)
        if response.status_code == 200:
            print(f"✅ /latest endpoint: {response.text}")
        else:
            print(f"⚠️ /latest endpoint: Status {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"❌ /latest endpoint: Connection timeout")
    except requests.exceptions.ConnectionError:
        print(f"❌ /latest endpoint: Connection refused")
    except Exception as e:
        print(f"❌ /latest endpoint: {e}")
    
    # Test stream endpoint
    try:
        response = requests.get(f"http://{current_ip}:81/stream", timeout=3, stream=True)
        print(f"✅ Stream endpoint: Status {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"❌ Stream endpoint: Connection timeout")
    except requests.exceptions.ConnectionError:
        print(f"❌ Stream endpoint: Connection refused")
    except Exception as e:
        print(f"❌ Stream endpoint: {e}")

# Step 3: Scan local network for ESP32
print("\n" + "="*70)
print("STEP 3: NETWORK SCAN (Finding ESP32)")
print("="*70)

print("\n[INFO] Scanning local network for ESP32-CAM...")
print("[INFO] This may take 30-60 seconds...")

# Get local IP range
try:
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"[INFO] Your computer IP: {local_ip}")
    
    # Extract network prefix (e.g., 192.168.137)
    network_prefix = '.'.join(local_ip.split('.')[:-1])
    print(f"[INFO] Scanning network: {network_prefix}.1-254")
    
    found_devices = []
    
    # Scan common IP range
    for i in range(1, 255):
        ip = f"{network_prefix}.{i}"
        
        # Skip your own IP
        if ip == local_ip:
            continue
        
        # Quick check - try to connect to port 80
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex((ip, 80))
            sock.close()
            
            if result == 0:
                # Port 80 is open, check if it's ESP32
                try:
                    response = requests.get(f"http://{ip}/", timeout=1)
                    # ESP32-CAM usually has "ESP32" in response
                    if response.status_code == 200:
                        found_devices.append(ip)
                        print(f"  ✓ Found device at {ip}")
                except:
                    pass
        except:
            pass
        
        # Progress indicator
        if i % 50 == 0:
            print(f"  ... scanned {i}/254")
    
    if found_devices:
        print(f"\n✅ Found {len(found_devices)} device(s) with web server:")
        for device_ip in found_devices:
            print(f"   • {device_ip}")
            
            # Test if it's ESP32-CAM
            try:
                response = requests.get(f"http://{device_ip}/latest", timeout=2)
                if response.status_code == 200:
                    print(f"     → This looks like ESP32-CAM! (has /latest endpoint)")
                    print(f"     → Latest event: {response.text}")
            except:
                pass
    else:
        print("\n❌ No devices found with web server on port 80")
        print("\nTroubleshooting:")
        print("  1. Make sure ESP32 is powered on")
        print("  2. Check ESP32 Serial Monitor for WiFi connection status")
        print("  3. Verify ESP32 is on the same network as your computer")
        print("  4. Check if ESP32 code has correct WiFi credentials")
        
except Exception as e:
    print(f"❌ Network scan failed: {e}")

# Step 4: Serial Monitor Check
print("\n" + "="*70)
print("STEP 4: SERIAL MONITOR CHECK")
print("="*70)

print("\n[INFO] To find ESP32 IP address:")
print("  1. Open Arduino IDE")
print("  2. Connect ESP32 via USB")
print("  3. Open Serial Monitor (Ctrl+Shift+M)")
print("  4. Set baud rate to 115200")
print("  5. Press ESP32 reset button")
print("  6. Look for lines like:")
print("     'WiFi connected'")
print("     'IP address: 192.168.x.x'")
print("  7. Update ESP32_IP in .env file with that IP")

# Step 5: Manual Test
print("\n" + "="*70)
print("STEP 5: MANUAL TEST")
print("="*70)

print("\n[INFO] Manual testing steps:")
print("  1. Open browser")
print(f"  2. Go to: http://{current_ip if current_ip else '192.168.x.x'}")
print("  3. You should see ESP32-CAM web interface")
print("  4. If not loading, IP is wrong")
print("")
print("  Alternative test:")
print(f"  • Stream: http://{current_ip if current_ip else '192.168.x.x'}:81/stream")
print(f"  • Latest: http://{current_ip if current_ip else '192.168.x.x'}/latest")

# Step 6: Common Issues
print("\n" + "="*70)
print("COMMON ISSUES & SOLUTIONS")
print("="*70)

print("""
1. CONNECTION TIMEOUT
   → ESP32 not powered on or not connected to WiFi
   → Check Serial Monitor for WiFi status
   
2. CONNECTION REFUSED
   → ESP32 web server not running
   → Re-upload ESP32 code
   
3. WRONG IP ADDRESS
   → ESP32 IP changed (DHCP)
   → Check Serial Monitor for current IP
   → Consider setting static IP in ESP32 code
   
4. FIREWALL BLOCKING
   → Windows Firewall blocking connection
   → Temporarily disable firewall to test
   
5. DIFFERENT NETWORK
   → Computer and ESP32 on different WiFi networks
   → Connect both to same network
   
6. ESP32 CRASHED
   → Press ESP32 reset button
   → Check Serial Monitor for errors
""")

# Summary
print("="*70)
print("SUMMARY")
print("="*70)

print(f"""
Current Configuration:
  ESP32_IP: {current_ip}
  
Next Steps:
  1. If ping failed → Check ESP32 power and WiFi
  2. If HTTP failed → Check ESP32 web server code
  3. If scan found devices → Update .env with correct IP
  4. If nothing works → Check Serial Monitor for ESP32 IP
  
After fixing, test with:
  python test_esp32_connection.py
""")

print("\n" + "="*70)
print("DEBUG COMPLETE".center(70))
print("="*70)
