"""
MASTER EVALUATION SCRIPT
Runs evaluation for all modules and generates combined report
"""

import json
from datetime import datetime
from evaluate_module2 import AccidentDetectionEvaluator
from evaluate_module3 import RearCollisionEvaluator
from evaluate_module4 import EmergencyAlertEvaluator

def generate_combined_report():
    """Generate combined evaluation report for all modules"""
    
    print("\n" + "="*70)
    print(" "*15 + "COMPLETE SYSTEM EVALUATION")
    print("="*70)
    
    # Module 2: Accident Detection
    print("\n[1/3] Evaluating Module 2: Accident Detection...")
    module2 = AccidentDetectionEvaluator()
    
    # Simulate tests (replace with real data)
    for i in range(25):
        module2.test_left_fall(detected=True, direction='LEFT', response_time=0.8)
    for i in range(25):
        module2.test_right_fall(detected=True, direction='RIGHT', response_time=0.9)
    for i in range(100):
        module2.test_normal_ride(false_alarm=False)
    
    metrics2 = module2.print_report()
    module2.save_results()
    
    # Module 3: Rear Collision Detection
    print("\n[2/3] Evaluating Module 3: Rear Collision Detection...")
    module3 = RearCollisionEvaluator()
    
    # Simulate tests (replace with real data)
    for i in range(50):
        module3.test_collision_zone(distance=3, detected=True, response_time=1.2, images_captured=True)
        module3.test_image_capture(3.5)
    for i in range(50):
        module3.test_warning_zone(distance=6, warned=True)
    for i in range(100):
        module3.test_safe_zone(distance=15, false_alarm=False)
    
    metrics3 = module3.print_report()
    module3.save_results()
    
    # Module 4: Emergency Alert System
    print("\n[3/3] Evaluating Module 4: Emergency Alert System...")
    module4 = EmergencyAlertEvaluator()
    
    # Simulate tests (replace with real data)
    for i in range(50):
        module4.test_alert_sent(success=True, delivery_time=32.5)
        module4.test_evidence_folder(created=True)
        module4.test_location_capture(captured=True, accurate=True)
        module4.test_metadata_creation(created=True, complete=True)
        module4.test_image_download(success=True, download_time=0.8)
        module4.test_image_download(success=True, download_time=0.9)
        module4.test_telegram_message(sent=True)
        module4.test_telegram_image(sent=True)
        module4.test_telegram_image(sent=True)
    
    metrics4 = module4.print_report()
    module4.save_results()
    
    # Generate combined summary
    print("\n" + "="*70)
    print(" "*20 + "OVERALL SYSTEM SUMMARY")
    print("="*70)
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'modules': {
            'Module 2 - Accident Detection': metrics2,
            'Module 3 - Rear Collision Detection': metrics3,
            'Module 4 - Emergency Alert System': metrics4
        }
    }
    
    # Save combined report
    with open('complete_evaluation_report.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n✓ Complete evaluation finished!")
    print("\nGenerated files:")
    print("  - module2_evaluation.json")
    print("  - module3_evaluation.json")
    print("  - module4_evaluation.json")
    print("  - complete_evaluation_report.json")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    generate_combined_report()
