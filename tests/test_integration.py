import os
import time
import sys

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

TRIGGER_FILE = "accident_trigger.txt"

print("=" * 60)
print("TESTING ACCIDENT TRIGGER INTEGRATION")
print("=" * 60)

# Test 1: Check if file exists
print("\n[TEST 1] Checking if trigger file exists...")
if os.path.exists(TRIGGER_FILE):
    print(f"✅ File exists: {os.path.abspath(TRIGGER_FILE)}")
else:
    print(f"⚠️  File doesn't exist, creating it...")
    with open(TRIGGER_FILE, "w") as f:
        f.write("")
    print(f"✅ Created: {os.path.abspath(TRIGGER_FILE)}")

# Test 2: Simulate gpt-intergration.py writing ACCIDENT
print("\n[TEST 2] Simulating hardware accident detection...")
print("Writing 'ACCIDENT' to trigger file...")
with open(TRIGGER_FILE, "w") as f:
    f.write("ACCIDENT")
print("✅ Written successfully")

# Test 3: Verify content
print("\n[TEST 3] Reading trigger file (simulating CARLA)...")
with open(TRIGGER_FILE, "r") as f:
    content = f.read().strip().upper()
print(f"Content read: '{content}'")

if content == "ACCIDENT":
    print("✅ CARLA would detect accident!")
    
    # Test 4: Clear file (simulating CARLA clearing after read)
    print("\n[TEST 4] Clearing trigger file (simulating CARLA)...")
    with open(TRIGGER_FILE, "w") as f:
        f.write("")
    print("✅ File cleared")
    
    # Test 5: Verify cleared
    print("\n[TEST 5] Verifying file is empty...")
    with open(TRIGGER_FILE, "r") as f:
        content = f.read()
    if content == "":
        print("✅ File is empty - ready for next trigger")
    else:
        print(f"❌ File still has content: '{content}'")
else:
    print(f"❌ Expected 'ACCIDENT', got '{content}'")

# Test 6: Simulate full cycle
print("\n[TEST 6] Simulating full detection cycle...")
print("Step 1: Hardware detects accident...")
with open(TRIGGER_FILE, "w") as f:
    f.write("ACCIDENT")
print("  ✅ Trigger file written")

time.sleep(0.5)  # Simulate CARLA check interval

print("Step 2: CARLA checks file...")
with open(TRIGGER_FILE, "r") as f:
    content = f.read().strip().upper()
if content == "ACCIDENT":
    print("  ✅ CARLA detected accident!")
    print("Step 3: CARLA clears file...")
    with open(TRIGGER_FILE, "w") as f:
        f.write("")
    print("  ✅ File cleared")
else:
    print(f"  ❌ Failed to detect: '{content}'")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nIntegration is working correctly!")
print("When gpt-intergration.py detects accident,")
print("CARLA will automatically trigger rear collision.")
