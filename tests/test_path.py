import os

# Test file paths
gpt_path = os.path.abspath(r"..\accident_trigger.txt")
carla_path = os.path.abspath(r"..\iot-python\accident_trigger.txt")

print("=== FILE PATH TEST ===")
print(f"GPT Integration path: {gpt_path}")
print(f"CARLA path: {carla_path}")
print(f"Paths match: {gpt_path == carla_path}")
print(f"\nFile exists: {os.path.exists(gpt_path)}")

# Test write and read
print("\n=== WRITE TEST ===")
with open(gpt_path, "w") as f:
    f.write("ACCIDENT")
print("Written: ACCIDENT")

print("\n=== READ TEST ===")
with open(carla_path, "r") as f:
    content = f.read()
print(f"Read: '{content}'")

# Clear
with open(gpt_path, "w") as f:
    f.write("")
print("\nCleared file")
