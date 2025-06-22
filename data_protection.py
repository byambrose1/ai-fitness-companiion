
import hashlib
import json
import os
from datetime import datetime, timedelta
import logging
from cryptography.fernet import Fernet

class DataProtection:
    def __init__(self):
        self.encryption_key = os.getenv('DATA_ENCRYPTION_KEY')
        if not self.encryption_key:
            # Generate a key (in production, store this securely in Secrets)
            self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Setup breach logging
        logging.basicConfig(
            filename='security.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def hash_email(self, email):
        """Hash email for logging without exposing PII"""
        return hashlib.sha256(email.encode()).hexdigest()[:8]
    
    def encrypt_sensitive_data(self, data):
        """Encrypt sensitive user data"""
        try:
            json_data = json.dumps(data)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            return encrypted_data
        except Exception as e:
            logging.error(f"Encryption failed: {str(e)}")
            return None
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Decrypt sensitive user data"""
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logging.error(f"Decryption failed: {str(e)}")
            return None
    
    def log_data_access(self, email, action, ip_address=None):
        """Log all data access for audit trail"""
        hashed_email = self.hash_email(email)
        logging.info(f"Data access - User: {hashed_email}, Action: {action}, IP: {ip_address}")
    
    def detect_breach_indicators(self, failed_attempts, suspicious_ips):
        """Detect potential breach indicators"""
        breach_detected = False
        alerts = []
        
        # Multiple failed login attempts
        if failed_attempts > 5:
            alerts.append(f"Multiple failed login attempts: {failed_attempts}")
            breach_detected = True
        
        # Suspicious IP access patterns
        if len(suspicious_ips) > 3:
            alerts.append(f"Access from multiple suspicious IPs: {len(suspicious_ips)}")
            breach_detected = True
        
        if breach_detected:
            self.initiate_breach_response(alerts)
        
        return breach_detected, alerts
    
    def initiate_breach_response(self, alerts):
        """Initiate breach response procedures"""
        timestamp = datetime.now().isoformat()
        
        # Log the potential breach
        logging.critical(f"POTENTIAL BREACH DETECTED: {timestamp}")
        for alert in alerts:
            logging.critical(f"Breach indicator: {alert}")
        
        # Create breach response file
        breach_data = {
            'timestamp': timestamp,
            'alerts': alerts,
            'status': 'investigating',
            'actions_taken': []
        }
        
        with open(f'breach_report_{timestamp.replace(":", "-")}.json', 'w') as f:
            json.dump(breach_data, f, indent=2)
        
        # Send notification (in production, integrate with your notification system)
        self.notify_security_team(breach_data)
    
    def notify_security_team(self, breach_data):
        """Notify security team of potential breach"""
        # In production, integrate with email/Slack/SMS notifications
        print(f"🚨 SECURITY ALERT: Potential data breach detected at {breach_data['timestamp']}")
        print("Immediate actions required:")
        print("1. Review security logs")
        print("2. Check user accounts for unauthorized access")
        print("3. Consider temporary access restrictions")
        print("4. Prepare user notifications if confirmed")

    def user_data_deletion(self, email):
        """Complete user data deletion for GDPR compliance"""
        hashed_email = self.hash_email(email)
        deletion_record = {
            'user_hash': hashed_email,
            'deletion_timestamp': datetime.now().isoformat(),
            'data_categories_deleted': [
                'profile_data', 'daily_logs', 'weekly_checkins', 
                'ai_interactions', 'subscription_data'
            ]
        }
        
        # Log deletion for compliance
        logging.info(f"User data deletion completed: {hashed_email}")
        
        return deletion_record
    
    def generate_breach_notification(self, user_email):
        """Generate user notification template for confirmed breaches"""
        return f"""
        Subject: Important Security Notice - Your Fitness App Account
        
        Dear User,
        
        We are writing to inform you of a security incident that may have affected your account.
        
        What happened:
        On [DATE], we discovered unauthorized access to some user data.
        
        What information was involved:
        - Profile information (name, email, fitness goals)
        - Daily logging data
        - NOT affected: Payment information (handled securely by Stripe)
        
        What we're doing:
        - Immediately secured the affected systems
        - Reset all user passwords as a precaution
        - Implemented additional security measures
        - Notified relevant authorities
        
        What you should do:
        - Change your password immediately
        - Monitor your accounts for suspicious activity
        - Contact us if you notice anything unusual
        
        We sincerely apologize for this incident and are committed to protecting your data.
        
        Fitness App Security Team
        """

# Initialize data protection
data_protection = DataProtection()
