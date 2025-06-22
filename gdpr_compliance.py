
from datetime import datetime, timedelta
import json

class GDPRCompliance:
    def __init__(self):
        self.data_retention_days = 1095  # 3 years default
        
    def handle_data_subject_request(self, email, request_type):
        """Handle GDPR data subject requests"""
        if request_type == "access":
            return self.export_user_data(email)
        elif request_type == "portability":
            return self.export_portable_data(email)
        elif request_type == "deletion":
            return self.delete_user_data(email)
        elif request_type == "rectification":
            return self.prepare_data_correction(email)
        
    def export_user_data(self, email):
        """Export all user data for GDPR access request"""
        if email not in users_data:
            return None
            
        user_data = users_data[email].copy()
        
        # Remove sensitive system data
        if 'password' in user_data:
            user_data['password'] = '[REDACTED]'
        if 'stripe_customer_id' in user_data:
            user_data['stripe_customer_id'] = '[REDACTED]'
            
        export_data = {
            'export_date': datetime.now().isoformat(),
            'user_data': user_data,
            'data_sources': [
                'profile_questionnaire',
                'daily_logs',
                'weekly_checkins',
                'ai_interactions',
                'subscription_data'
            ]
        }
        
        return export_data
    
    def delete_user_data(self, email):
        """Complete user data deletion for GDPR right to erasure"""
        if email not in users_data:
            return {"status": "user_not_found"}
            
        # Create deletion record before removing data
        deletion_record = {
            'email_hash': data_protection.hash_email(email),
            'deletion_date': datetime.now().isoformat(),
            'data_deleted': True,
            'retention_required': False  # Set to True if legal requirement to retain some data
        }
        
        # Remove user data
        del users_data[email]
        
        # Log deletion
        with open('gdpr_deletions.json', 'a') as f:
            f.write(json.dumps(deletion_record) + '\n')
            
        return {"status": "deleted", "confirmation": deletion_record}
    
    def check_data_retention_compliance(self):
        """Check and clean up data past retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)
        expired_users = []
        
        for email, user_data in list(users_data.items()):
            created_date = datetime.fromisoformat(user_data.get('created_at', ''))
            if created_date < cutoff_date:
                # Check if user has been active recently
                last_activity = self.get_last_activity_date(user_data)
                if last_activity and last_activity < cutoff_date:
                    expired_users.append(email)
        
        return expired_users
    
    def get_last_activity_date(self, user_data):
        """Get user's last activity date"""
        dates = []
        
        # Check daily logs
        if user_data.get('daily_logs'):
            for log in user_data['daily_logs']:
                if log.get('timestamp'):
                    dates.append(datetime.fromisoformat(log['timestamp']))
        
        # Check weekly checkins
        if user_data.get('weekly_checkins'):
            for checkin in user_data['weekly_checkins']:
                if checkin.get('timestamp'):
                    dates.append(datetime.fromisoformat(checkin['timestamp']))
        
        return max(dates) if dates else None

gdpr_compliance = GDPRCompliance()
