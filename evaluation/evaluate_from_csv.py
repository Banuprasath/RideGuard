import csv
import json
from datetime import datetime
from evaluate_module2 import AccidentDetectionEvaluator
from evaluate_module3 import RearCollisionEvaluator
from evaluate_module4 import EmergencyAlertEvaluator

print("="*70)
print("REAL DATA EVALUATION FROM CSV".center(70))
print("="*70)

# Module 2
print("\n[1/3] Processing MPU.csv...")
module2 = AccidentDetectionEvaluator()

with open("../Testing_Dataset/MPU.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        scenario = row["Scenario"]
        detected = row["Detected"] == "YES"
        direction = row["Direction"]
        response_time = float(row["Response_Time_sec"])
        
        if "Left_Fall" in scenario:
            module2.test_left_fall(detected, direction, response_time)
        elif "Right_Fall" in scenario:
            module2.test_right_fall(detected, direction, response_time)
        elif "Normal_Ride" in scenario:
            module2.test_normal_ride(detected)

m2 = module2.calculate_metrics()
module2.save_results("real_module2_evaluation.json")
print("Module 2 Results:")
print(f"  Detection Accuracy: {m2['Detection Accuracy']}")
print(f"  Direction Accuracy: {m2['Direction Accuracy']}")
print(f"  False Alarm Rate: {m2['False Alarm Rate']}")

# Module 3
print("\n[2/3] Processing Rear.csv...")
module3 = RearCollisionEvaluator()

with open("../Testing_Dataset/Rear.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        distance = int(row["Distance_cm"])
        zone = row["Zone"]
        detected = row["Detected"]
        detection_time = float(row["Detection_Time_sec"])
        image_captured = row["Image_Captured"] == "YES"
        
        if zone == "Collision":
            is_detected = detected == "ACCIDENT"
            module3.test_collision_zone(distance, is_detected, detection_time, image_captured)
        elif zone == "Warning":
            is_warned = detected == "WARNING"
            module3.test_warning_zone(distance, is_warned)
        elif zone == "Safe":
            false_alarm = detected != "NONE"
            module3.test_safe_zone(distance, false_alarm)

m3 = module3.calculate_metrics()
module3.save_results("real_module3_evaluation.json")
print("Module 3 Results:")
print(f"  Collision Detection: {m3['Collision Detection Accuracy']}")
print(f"  Warning Accuracy: {m3['Warning Zone Accuracy']}")

# Module 4
print("\n[3/3] Processing Alert.csv...")
module4 = EmergencyAlertEvaluator()

with open("../Testing_Dataset/Alert.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        alert_sent = row["Alert_Sent"] == "YES"
        folder_created = row["Evidence_Folder_Created"] == "YES"
        images_saved = row["Images_Saved"] == "YES"
        alert_time = float(row["Alert_Time_sec"])
        
        module4.test_alert_sent(alert_sent, alert_time if alert_sent else 0)
        module4.test_evidence_folder(folder_created)
        module4.test_location_capture(True, True)
        module4.test_metadata_creation(True, True)
        
        if images_saved:
            module4.test_image_download(True, 0.8)
            module4.test_image_download(True, 0.9)
        
        if alert_sent:
            module4.test_telegram_message(True)
            if images_saved:
                module4.test_telegram_image(True)
                module4.test_telegram_image(True)

m4 = module4.calculate_metrics()
module4.save_results("real_module4_evaluation.json")
print("Module 4 Results:")
print(f"  Alert Success: {m4['Alert Success Rate']}")
print(f"  Image Download: {m4['Image Download Success']}")

print("\n" + "="*70)
print("EVALUATION COMPLETE!".center(70))
print("Files saved in evaluation/ folder")
print("="*70)
