
from datetime import datetime, timedelta
import json

class SmartNotifications:
    def __init__(self):
        self.notification_patterns = {
            'morning_log': {
                'time': '09:00',
                'message': "☀️ Good morning! Ready to log yesterday's wins?",
                'condition': 'missed_yesterday'
            },
            'evening_reminder': {
                'time': '20:00', 
                'message': "🌙 Quick 2-minute check-in before bed?",
                'condition': 'no_log_today'
            },
            'streak_protection': {
                'time': '22:00',
                'message': "🔥 Don't break that {streak_days}-day streak! Quick log?",
                'condition': 'streak_at_risk'
            },
            'habit_stack': {
                'time': 'user_preference',
                'message': "💡 After you {habit_anchor}, remember to log your day!",
                'condition': 'habit_reminder'
            }
        }
    
    def generate_contextual_reminder(self, user_data):
        """Generate personalized reminder based on user patterns"""
        daily_logs = user_data.get('daily_logs', [])
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if user logged today
        logged_today = any(log.get('date') == today for log in daily_logs)
        
        if not logged_today:
            # Check user's typical logging time
            log_times = []
            for log in daily_logs[-5:]:  # Last 5 logs
                if 'timestamp' in log:
                    log_time = datetime.fromisoformat(log['timestamp']).hour
                    log_times.append(log_time)
            
            if log_times:
                avg_time = sum(log_times) / len(log_times)
                if avg_time < 12:  # Morning logger
                    return {
                        'message': "☀️ Morning person! Ready for your daily check-in?",
                        'suggested_time': '09:00'
                    }
                else:  # Evening logger
                    return {
                        'message': "🌙 End your day with a quick 2-minute log?",
                        'suggested_time': '20:00'
                    }
        
        return None
    
    def get_streak_motivation(self, streak_days):
        """Get streak-specific motivational messages"""
        if streak_days >= 30:
            return "🏆 30+ day champion! You're building life-changing habits!"
        elif streak_days >= 14:
            return "💪 Two weeks strong! You're in the habit formation zone!"
        elif streak_days >= 7:
            return "🔥 One week streak! Your consistency is paying off!"
        elif streak_days >= 3:
            return "⭐ Great momentum! Keep the streak alive!"
        else:
            return "🌱 Every day counts! You're building something amazing!"

smart_notifications = SmartNotifications()
