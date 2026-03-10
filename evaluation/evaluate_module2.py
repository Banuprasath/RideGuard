"""
MODULE 2: ACCIDENT DETECTION EVALUATION
Tests tilt-based accident detection accuracy
"""

import time
import json
from datetime import datetime

class AccidentDetectionEvaluator:
    def __init__(self):
        self.results = {
            'left_falls': {'total': 0, 'detected': 0, 'correct_direction': 0, 'response_times': []},
            'right_falls': {'total': 0, 'detected': 0, 'correct_direction': 0, 'response_times': []},
            'normal_rides': {'total': 0, 'false_alarms': 0},
            'threshold_tests': []
        }
    
    def test_left_fall(self, detected, direction, response_time):
        """Test left fall detection"""
        self.results['left_falls']['total'] += 1
        if detected:
            self.results['left_falls']['detected'] += 1
            if direction == 'LEFT':
                self.results['left_falls']['correct_direction'] += 1
            self.results['left_falls']['response_times'].append(response_time)
    
    def test_right_fall(self, detected, direction, response_time):
        """Test right fall detection"""
        self.results['right_falls']['total'] += 1
        if detected:
            self.results['right_falls']['detected'] += 1
            if direction == 'RIGHT':
                self.results['right_falls']['correct_direction'] += 1
            self.results['right_falls']['response_times'].append(response_time)
    
    def test_normal_ride(self, false_alarm):
        """Test normal riding (should NOT trigger)"""
        self.results['normal_rides']['total'] += 1
        if false_alarm:
            self.results['normal_rides']['false_alarms'] += 1
    
    def test_threshold(self, angle, detected):
        """Test detection at different angles"""
        self.results['threshold_tests'].append({
            'angle': angle,
            'detected': detected
        })
    
    def calculate_metrics(self):
        """Calculate all metrics"""
        # Total falls
        total_falls = self.results['left_falls']['total'] + self.results['right_falls']['total']
        total_detected = self.results['left_falls']['detected'] + self.results['right_falls']['detected']
        total_correct_dir = self.results['left_falls']['correct_direction'] + self.results['right_falls']['correct_direction']
        
        # Detection Accuracy
        detection_accuracy = (total_detected / total_falls * 100) if total_falls > 0 else 0
        
        # Direction Accuracy
        direction_accuracy = (total_correct_dir / total_detected * 100) if total_detected > 0 else 0
        
        # False Alarm Rate
        false_alarm_rate = (self.results['normal_rides']['false_alarms'] / 
                           self.results['normal_rides']['total'] * 100) if self.results['normal_rides']['total'] > 0 else 0
        
        # Average Response Time
        all_times = self.results['left_falls']['response_times'] + self.results['right_falls']['response_times']
        avg_response_time = sum(all_times) / len(all_times) if all_times else 0
        
        metrics = {
            'Detection Accuracy': f"{detection_accuracy:.2f}%",
            'Direction Accuracy': f"{direction_accuracy:.2f}%",
            'False Alarm Rate': f"{false_alarm_rate:.2f}%",
            'Average Response Time': f"{avg_response_time:.3f}s",
            'Total Tests': total_falls + self.results['normal_rides']['total'],
            'Falls Detected': f"{total_detected}/{total_falls}",
            'Correct Direction': f"{total_correct_dir}/{total_detected}",
            'False Alarms': f"{self.results['normal_rides']['false_alarms']}/{self.results['normal_rides']['total']}"
        }
        
        return metrics
    
    def print_report(self):
        """Print evaluation report"""
        metrics = self.calculate_metrics()
        
        print("\n" + "="*60)
        print("MODULE 2: ACCIDENT DETECTION EVALUATION REPORT")
        print("="*60)
        print(f"\n{'Metric':<30} {'Result':<15} {'Target':<10}")
        print("-"*60)
        print(f"{'Detection Accuracy':<30} {metrics['Detection Accuracy']:<15} {'≥95%':<10}")
        print(f"{'Direction Accuracy':<30} {metrics['Direction Accuracy']:<15} {'≥90%':<10}")
        print(f"{'False Alarm Rate':<30} {metrics['False Alarm Rate']:<15} {'≤5%':<10}")
        print(f"{'Average Response Time':<30} {metrics['Average Response Time']:<15} {'≤1.0s':<10}")
        print("-"*60)
        print(f"\nDetailed Results:")
        print(f"  Total Tests: {metrics['Total Tests']}")
        print(f"  Falls Detected: {metrics['Falls Detected']}")
        print(f"  Correct Direction: {metrics['Correct Direction']}")
        print(f"  False Alarms: {metrics['False Alarms']}")
        print("="*60 + "\n")
        
        return metrics
    
    def save_results(self, filename="module2_evaluation.json"):
        """Save results to JSON file"""
        metrics = self.calculate_metrics()
        output = {
            'timestamp': datetime.now().isoformat(),
            'module': 'Accident Detection (Module 2)',
            'metrics': metrics,
            'raw_data': self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Results saved to {filename}")


# ============= EXAMPLE USAGE =============
if __name__ == "__main__":
    evaluator = AccidentDetectionEvaluator()
    
    print("Starting Module 2 Evaluation...")
    print("Simulate tests by calling evaluator methods\n")
    
    # Example: Simulate 25 left falls
    print("Testing LEFT falls...")
    for i in range(25):
        detected = True  # Simulated detection
        direction = 'LEFT'  # Simulated direction
        response_time = 0.8  # Simulated response time
        evaluator.test_left_fall(detected, direction, response_time)
    
    # Example: Simulate 25 right falls
    print("Testing RIGHT falls...")
    for i in range(25):
        detected = True
        direction = 'RIGHT'
        response_time = 0.9
        evaluator.test_right_fall(detected, direction, response_time)
    
    # Example: Simulate 100 normal rides
    print("Testing NORMAL rides...")
    for i in range(100):
        false_alarm = False  # Should be False for normal rides
        evaluator.test_normal_ride(false_alarm)
    
    # Print report
    evaluator.print_report()
    evaluator.save_results()
    
    print("\n✓ Evaluation complete!")
    print("\nTo use with real data:")
    print("1. Integrate with fall_status.txt monitoring")
    print("2. Record actual detection results")
    print("3. Measure response times with timestamps")
