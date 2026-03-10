"""
MODULE 4: EMERGENCY ALERT SYSTEM EVALUATION
Tests evidence logging, image download, and Telegram alerts
"""

import time
import json
import os
from datetime import datetime

class EmergencyAlertEvaluator:
    def __init__(self):
        self.results = {
            'alerts': {'total': 0, 'sent': 0, 'failed': 0, 'delivery_times': []},
            'images': {'download_attempts': 0, 'success': 0, 'failed': 0, 'download_times': []},
            'metadata': {'created': 0, 'complete': 0, 'incomplete': 0},
            'location': {'captured': 0, 'accurate': 0},
            'evidence_folders': {'created': 0, 'failed': 0},
            'telegram': {'message_sent': 0, 'message_failed': 0, 'images_sent': 0, 'images_failed': 0}
        }
    
    def test_alert_sent(self, success, delivery_time):
        """Test alert sending"""
        self.results['alerts']['total'] += 1
        if success:
            self.results['alerts']['sent'] += 1
            self.results['alerts']['delivery_times'].append(delivery_time)
        else:
            self.results['alerts']['failed'] += 1
    
    def test_image_download(self, success, download_time):
        """Test image download from ESP32"""
        self.results['images']['download_attempts'] += 1
        if success:
            self.results['images']['success'] += 1
            self.results['images']['download_times'].append(download_time)
        else:
            self.results['images']['failed'] += 1
    
    def test_metadata_creation(self, created, complete):
        """Test metadata file creation"""
        if created:
            self.results['metadata']['created'] += 1
            if complete:
                self.results['metadata']['complete'] += 1
            else:
                self.results['metadata']['incomplete'] += 1
    
    def test_location_capture(self, captured, accurate):
        """Test location capture"""
        if captured:
            self.results['location']['captured'] += 1
            if accurate:
                self.results['location']['accurate'] += 1
    
    def test_evidence_folder(self, created):
        """Test evidence folder creation"""
        if created:
            self.results['evidence_folders']['created'] += 1
        else:
            self.results['evidence_folders']['failed'] += 1
    
    def test_telegram_message(self, sent):
        """Test Telegram message"""
        if sent:
            self.results['telegram']['message_sent'] += 1
        else:
            self.results['telegram']['message_failed'] += 1
    
    def test_telegram_image(self, sent):
        """Test Telegram image"""
        if sent:
            self.results['telegram']['images_sent'] += 1
        else:
            self.results['telegram']['images_failed'] += 1
    
    def calculate_metrics(self):
        """Calculate all metrics"""
        # Alert Success Rate
        alert_success_rate = (self.results['alerts']['sent'] / 
                             self.results['alerts']['total'] * 100) if self.results['alerts']['total'] > 0 else 0
        
        # Image Download Success Rate
        image_success_rate = (self.results['images']['success'] / 
                             self.results['images']['download_attempts'] * 100) if self.results['images']['download_attempts'] > 0 else 0
        
        # Average Delivery Time
        avg_delivery_time = (sum(self.results['alerts']['delivery_times']) / 
                            len(self.results['alerts']['delivery_times'])) if self.results['alerts']['delivery_times'] else 0
        
        # Average Download Time
        avg_download_time = (sum(self.results['images']['download_times']) / 
                            len(self.results['images']['download_times'])) if self.results['images']['download_times'] else 0
        
        # Metadata Completeness
        metadata_completeness = (self.results['metadata']['complete'] / 
                                self.results['metadata']['created'] * 100) if self.results['metadata']['created'] > 0 else 0
        
        # Location Accuracy
        location_accuracy = (self.results['location']['accurate'] / 
                            self.results['location']['captured'] * 100) if self.results['location']['captured'] > 0 else 0
        
        # Evidence Folder Success
        folder_success = (self.results['evidence_folders']['created'] / 
                         (self.results['evidence_folders']['created'] + self.results['evidence_folders']['failed']) * 100) if (self.results['evidence_folders']['created'] + self.results['evidence_folders']['failed']) > 0 else 0
        
        # Telegram Success Rate
        telegram_message_success = (self.results['telegram']['message_sent'] / 
                                   (self.results['telegram']['message_sent'] + self.results['telegram']['message_failed']) * 100) if (self.results['telegram']['message_sent'] + self.results['telegram']['message_failed']) > 0 else 0
        
        telegram_image_success = (self.results['telegram']['images_sent'] / 
                                 (self.results['telegram']['images_sent'] + self.results['telegram']['images_failed']) * 100) if (self.results['telegram']['images_sent'] + self.results['telegram']['images_failed']) > 0 else 0
        
        metrics = {
            'Alert Success Rate': f"{alert_success_rate:.2f}%",
            'Image Download Success': f"{image_success_rate:.2f}%",
            'Average Delivery Time': f"{avg_delivery_time:.2f}s",
            'Average Download Time': f"{avg_download_time:.3f}s",
            'Metadata Completeness': f"{metadata_completeness:.2f}%",
            'Location Accuracy': f"{location_accuracy:.2f}%",
            'Evidence Folder Success': f"{folder_success:.2f}%",
            'Telegram Message Success': f"{telegram_message_success:.2f}%",
            'Telegram Image Success': f"{telegram_image_success:.2f}%",
            'Total Alerts': self.results['alerts']['total'],
            'Alerts Sent': f"{self.results['alerts']['sent']}/{self.results['alerts']['total']}",
            'Images Downloaded': f"{self.results['images']['success']}/{self.results['images']['download_attempts']}",
            'Metadata Complete': f"{self.results['metadata']['complete']}/{self.results['metadata']['created']}",
            'Telegram Messages': f"{self.results['telegram']['message_sent']}/{self.results['telegram']['message_sent'] + self.results['telegram']['message_failed']}",
            'Telegram Images': f"{self.results['telegram']['images_sent']}/{self.results['telegram']['images_sent'] + self.results['telegram']['images_failed']}"
        }
        
        return metrics
    
    def print_report(self):
        """Print evaluation report"""
        metrics = self.calculate_metrics()
        
        print("\n" + "="*60)
        print("MODULE 4: EMERGENCY ALERT SYSTEM EVALUATION REPORT")
        print("="*60)
        print(f"\n{'Metric':<35} {'Result':<15} {'Target':<10}")
        print("-"*60)
        print(f"{'Alert Success Rate':<35} {metrics['Alert Success Rate']:<15} {'≥98%':<10}")
        print(f"{'Image Download Success':<35} {metrics['Image Download Success']:<15} {'≥90%':<10}")
        print(f"{'Average Delivery Time':<35} {metrics['Average Delivery Time']:<15} {'≤35s':<10}")
        print(f"{'Average Download Time':<35} {metrics['Average Download Time']:<15} {'≤2.0s':<10}")
        print(f"{'Metadata Completeness':<35} {metrics['Metadata Completeness']:<15} {'100%':<10}")
        print(f"{'Location Accuracy':<35} {metrics['Location Accuracy']:<15} {'≥95%':<10}")
        print(f"{'Evidence Folder Success':<35} {metrics['Evidence Folder Success']:<15} {'100%':<10}")
        print(f"{'Telegram Message Success':<35} {metrics['Telegram Message Success']:<15} {'≥98%':<10}")
        print(f"{'Telegram Image Success':<35} {metrics['Telegram Image Success']:<15} {'≥95%':<10}")
        print("-"*60)
        print(f"\nDetailed Results:")
        print(f"  Total Alerts: {metrics['Total Alerts']}")
        print(f"  Alerts Sent: {metrics['Alerts Sent']}")
        print(f"  Images Downloaded: {metrics['Images Downloaded']}")
        print(f"  Metadata Complete: {metrics['Metadata Complete']}")
        print(f"  Telegram Messages: {metrics['Telegram Messages']}")
        print(f"  Telegram Images: {metrics['Telegram Images']}")
        print("="*60 + "\n")
        
        return metrics
    
    def save_results(self, filename="module4_evaluation.json"):
        """Save results to JSON file"""
        metrics = self.calculate_metrics()
        output = {
            'timestamp': datetime.now().isoformat(),
            'module': 'Emergency Alert System (Module 4)',
            'metrics': metrics,
            'raw_data': self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Results saved to {filename}")


# ============= EXAMPLE USAGE =============
if __name__ == "__main__":
    evaluator = EmergencyAlertEvaluator()
    
    print("Starting Module 4 Evaluation...")
    print("Simulate tests by calling evaluator methods\n")
    
    # Example: Test 50 alerts
    print("Testing ALERT system...")
    for i in range(50):
        success = True  # Alert sent successfully
        delivery_time = 32.5  # 32.5 seconds
        evaluator.test_alert_sent(success, delivery_time)
        
        # Test evidence folder
        evaluator.test_evidence_folder(created=True)
        
        # Test location capture
        evaluator.test_location_capture(captured=True, accurate=True)
        
        # Test metadata
        evaluator.test_metadata_creation(created=True, complete=True)
        
        # Test image downloads (2 images per accident)
        evaluator.test_image_download(success=True, download_time=0.8)
        evaluator.test_image_download(success=True, download_time=0.9)
        
        # Test Telegram
        evaluator.test_telegram_message(sent=True)
        evaluator.test_telegram_image(sent=True)
        evaluator.test_telegram_image(sent=True)
    
    # Print report
    evaluator.print_report()
    evaluator.save_results()
    
    print("\n✓ Evaluation complete!")
    print("\nTo use with real data:")
    print("1. Monitor emergency_alert.py debug logs")
    print("2. Check records/ folder for evidence")
    print("3. Verify Telegram message delivery")
    print("4. Measure actual delivery times")
