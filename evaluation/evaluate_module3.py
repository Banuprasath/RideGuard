"""
MODULE 3: REAR COLLISION DETECTION EVALUATION
Tests ultrasonic sensor + ESP32-CAM accuracy
"""

import time
import json
from datetime import datetime

class RearCollisionEvaluator:
    def __init__(self):
        self.results = {
            'collision_zone': {'total': 0, 'detected': 0, 'response_times': []},  # ≤4cm
            'warning_zone': {'total': 0, 'warned': 0},  # 5-7cm
            'safe_zone': {'total': 0, 'false_alarms': 0},  # >7cm
            'image_capture': {'attempts': 0, 'success': 0, 'capture_times': []},
            'distance_readings': []
        }
    
    def test_collision_zone(self, distance, detected, response_time, images_captured):
        """Test collision zone (≤4cm)"""
        self.results['collision_zone']['total'] += 1
        if detected:
            self.results['collision_zone']['detected'] += 1
            self.results['collision_zone']['response_times'].append(response_time)
        
        if detected:
            self.results['image_capture']['attempts'] += 1
            if images_captured:
                self.results['image_capture']['success'] += 1
        
        self.results['distance_readings'].append({
            'distance': distance,
            'zone': 'collision',
            'detected': detected
        })
    
    def test_warning_zone(self, distance, warned):
        """Test warning zone (5-7cm)"""
        self.results['warning_zone']['total'] += 1
        if warned:
            self.results['warning_zone']['warned'] += 1
        
        self.results['distance_readings'].append({
            'distance': distance,
            'zone': 'warning',
            'warned': warned
        })
    
    def test_safe_zone(self, distance, false_alarm):
        """Test safe zone (>7cm)"""
        self.results['safe_zone']['total'] += 1
        if false_alarm:
            self.results['safe_zone']['false_alarms'] += 1
        
        self.results['distance_readings'].append({
            'distance': distance,
            'zone': 'safe',
            'false_alarm': false_alarm
        })
    
    def test_image_capture(self, capture_time):
        """Test ESP32 image capture time"""
        self.results['image_capture']['capture_times'].append(capture_time)
    
    def calculate_metrics(self):
        """Calculate all metrics"""
        # Collision Detection Accuracy
        collision_accuracy = (self.results['collision_zone']['detected'] / 
                             self.results['collision_zone']['total'] * 100) if self.results['collision_zone']['total'] > 0 else 0
        
        # Warning Zone Accuracy
        warning_accuracy = (self.results['warning_zone']['warned'] / 
                           self.results['warning_zone']['total'] * 100) if self.results['warning_zone']['total'] > 0 else 0
        
        # False Positive Rate
        false_positive_rate = (self.results['safe_zone']['false_alarms'] / 
                              self.results['safe_zone']['total'] * 100) if self.results['safe_zone']['total'] > 0 else 0
        
        # Average Response Time
        avg_response_time = (sum(self.results['collision_zone']['response_times']) / 
                            len(self.results['collision_zone']['response_times'])) if self.results['collision_zone']['response_times'] else 0
        
        # Image Capture Success Rate
        image_success_rate = (self.results['image_capture']['success'] / 
                             self.results['image_capture']['attempts'] * 100) if self.results['image_capture']['attempts'] > 0 else 0
        
        # Average Image Capture Time
        avg_capture_time = (sum(self.results['image_capture']['capture_times']) / 
                           len(self.results['image_capture']['capture_times'])) if self.results['image_capture']['capture_times'] else 0
        
        metrics = {
            'Collision Detection Accuracy': f"{collision_accuracy:.2f}%",
            'Warning Zone Accuracy': f"{warning_accuracy:.2f}%",
            'False Positive Rate': f"{false_positive_rate:.2f}%",
            'Average Response Time': f"{avg_response_time:.3f}s",
            'Image Capture Success': f"{image_success_rate:.2f}%",
            'Average Capture Time': f"{avg_capture_time:.3f}s",
            'Total Tests': (self.results['collision_zone']['total'] + 
                          self.results['warning_zone']['total'] + 
                          self.results['safe_zone']['total']),
            'Collisions Detected': f"{self.results['collision_zone']['detected']}/{self.results['collision_zone']['total']}",
            'Warnings Issued': f"{self.results['warning_zone']['warned']}/{self.results['warning_zone']['total']}",
            'False Alarms': f"{self.results['safe_zone']['false_alarms']}/{self.results['safe_zone']['total']}",
            'Images Captured': f"{self.results['image_capture']['success']}/{self.results['image_capture']['attempts']}"
        }
        
        return metrics
    
    def print_report(self):
        """Print evaluation report"""
        metrics = self.calculate_metrics()
        
        print("\n" + "="*60)
        print("MODULE 3: REAR COLLISION DETECTION EVALUATION REPORT")
        print("="*60)
        print(f"\n{'Metric':<35} {'Result':<15} {'Target':<10}")
        print("-"*60)
        print(f"{'Collision Detection Accuracy':<35} {metrics['Collision Detection Accuracy']:<15} {'≥95%':<10}")
        print(f"{'Warning Zone Accuracy':<35} {metrics['Warning Zone Accuracy']:<15} {'≥90%':<10}")
        print(f"{'False Positive Rate':<35} {metrics['False Positive Rate']:<15} {'≤5%':<10}")
        print(f"{'Average Response Time':<35} {metrics['Average Response Time']:<15} {'≤1.5s':<10}")
        print(f"{'Image Capture Success':<35} {metrics['Image Capture Success']:<15} {'≥95%':<10}")
        print(f"{'Average Capture Time':<35} {metrics['Average Capture Time']:<15} {'≤4.0s':<10}")
        print("-"*60)
        print(f"\nDetailed Results:")
        print(f"  Total Tests: {metrics['Total Tests']}")
        print(f"  Collisions Detected: {metrics['Collisions Detected']}")
        print(f"  Warnings Issued: {metrics['Warnings Issued']}")
        print(f"  False Alarms: {metrics['False Alarms']}")
        print(f"  Images Captured: {metrics['Images Captured']}")
        print("="*60 + "\n")
        
        return metrics
    
    def save_results(self, filename="module3_evaluation.json"):
        """Save results to JSON file"""
        metrics = self.calculate_metrics()
        output = {
            'timestamp': datetime.now().isoformat(),
            'module': 'Rear Collision Detection (Module 3)',
            'metrics': metrics,
            'raw_data': self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Results saved to {filename}")


# ============= EXAMPLE USAGE =============
if __name__ == "__main__":
    evaluator = RearCollisionEvaluator()
    
    print("Starting Module 3 Evaluation...")
    print("Simulate tests by calling evaluator methods\n")
    
    # Example: Test collision zone (≤4cm)
    print("Testing COLLISION zone (≤4cm)...")
    for i in range(50):
        distance = 3  # 3cm
        detected = True
        response_time = 1.2
        images_captured = True
        evaluator.test_collision_zone(distance, detected, response_time, images_captured)
        evaluator.test_image_capture(3.5)  # 3.5s to capture 5 images
    
    # Example: Test warning zone (5-7cm)
    print("Testing WARNING zone (5-7cm)...")
    for i in range(50):
        distance = 6  # 6cm
        warned = True
        evaluator.test_warning_zone(distance, warned)
    
    # Example: Test safe zone (>7cm)
    print("Testing SAFE zone (>7cm)...")
    for i in range(100):
        distance = 15  # 15cm
        false_alarm = False
        evaluator.test_safe_zone(distance, false_alarm)
    
    # Print report
    evaluator.print_report()
    evaluator.save_results()
    
    print("\n✓ Evaluation complete!")
    print("\nTo use with real data:")
    print("1. Monitor Arduino serial output (DIST:XX)")
    print("2. Record detection results from accident_trigger.txt")
    print("3. Check ESP32 image capture success")
    print("4. Measure response times with timestamps")
