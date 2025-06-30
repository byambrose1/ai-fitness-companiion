
import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class FitnessTrackerAPI:
    """Unified fitness tracker API integration"""
    
    def __init__(self):
        # API Keys from environment variables
        self.fitbit_client_id = os.getenv('FITBIT_CLIENT_ID')
        self.fitbit_client_secret = os.getenv('FITBIT_CLIENT_SECRET')
        self.oura_api_key = os.getenv('OURA_API_KEY')
        self.garmin_consumer_key = os.getenv('GARMIN_CONSUMER_KEY')
        self.garmin_consumer_secret = os.getenv('GARMIN_CONSUMER_SECRET')
        self.google_fit_client_id = os.getenv('GOOGLE_FIT_CLIENT_ID')
        self.google_fit_client_secret = os.getenv('GOOGLE_FIT_CLIENT_SECRET')
        
    def sync_fitbit_data(self, access_token: str, date: str = None) -> Dict:
        """Sync data from Fitbit API"""
        if not self.fitbit_client_id:
            return {"error": "Fitbit API not configured"}
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        try:
            # Get activity data
            activity_url = f'https://api.fitbit.com/1/user/-/activities/date/{date}.json'
            activity_response = requests.get(activity_url, headers=headers)
            
            # Get sleep data
            sleep_url = f'https://api.fitbit.com/1.2/user/-/sleep/date/{date}.json'
            sleep_response = requests.get(sleep_url, headers=headers)
            
            # Get heart rate data
            hr_url = f'https://api.fitbit.com/1/user/-/activities/heart/date/{date}/1d.json'
            hr_response = requests.get(hr_url, headers=headers)
            
            if activity_response.status_code == 200:
                activity_data = activity_response.json()
                sleep_data = sleep_response.json() if sleep_response.status_code == 200 else {}
                hr_data = hr_response.json() if hr_response.status_code == 200 else {}
                
                return {
                    'source': 'Fitbit',
                    'date': date,
                    'steps': activity_data.get('summary', {}).get('steps', 0),
                    'distance': activity_data.get('summary', {}).get('distances', [{}])[0].get('distance', 0),
                    'calories': activity_data.get('summary', {}).get('caloriesOut', 0),
                    'active_minutes': activity_data.get('summary', {}).get('veryActiveMinutes', 0),
                    'sleep_hours': self._extract_fitbit_sleep_hours(sleep_data),
                    'sleep_score': self._extract_fitbit_sleep_score(sleep_data),
                    'resting_heart_rate': self._extract_fitbit_resting_hr(hr_data),
                    'raw_data': {
                        'activity': activity_data,
                        'sleep': sleep_data,
                        'heart_rate': hr_data
                    }
                }
            else:
                return {"error": f"Fitbit API error: {activity_response.status_code}"}
                
        except Exception as e:
            return {"error": f"Fitbit sync failed: {str(e)}"}
    
    def sync_oura_data(self, access_token: str, date: str = None) -> Dict:
        """Sync data from Oura Ring API"""
        if not self.oura_api_key:
            return {"error": "Oura API not configured"}
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Get daily activity
            activity_url = f'https://api.ouraring.com/v2/usercollection/daily_activity'
            activity_params = {'start_date': date, 'end_date': date}
            activity_response = requests.get(activity_url, headers=headers, params=activity_params)
            
            # Get sleep data
            sleep_url = f'https://api.ouraring.com/v2/usercollection/daily_sleep'
            sleep_response = requests.get(sleep_url, headers=headers, params=activity_params)
            
            # Get readiness data
            readiness_url = f'https://api.ouraring.com/v2/usercollection/daily_readiness'
            readiness_response = requests.get(readiness_url, headers=headers, params=activity_params)
            
            if activity_response.status_code == 200:
                activity_data = activity_response.json()
                sleep_data = sleep_response.json() if sleep_response.status_code == 200 else {}
                readiness_data = readiness_response.json() if readiness_response.status_code == 200 else {}
                
                # Extract data from first record of the day
                activity_record = activity_data.get('data', [{}])[0] if activity_data.get('data') else {}
                sleep_record = sleep_data.get('data', [{}])[0] if sleep_data.get('data') else {}
                readiness_record = readiness_data.get('data', [{}])[0] if readiness_data.get('data') else {}
                
                return {
                    'source': 'Oura Ring',
                    'date': date,
                    'steps': activity_record.get('steps', 0),
                    'calories': activity_record.get('active_calories', 0),
                    'sleep_hours': sleep_record.get('total_sleep_duration', 0) / 3600,  # Convert seconds to hours
                    'sleep_score': sleep_record.get('score', 0),
                    'readiness_score': readiness_record.get('score', 0),
                    'hrv': readiness_record.get('hrv_average', 0),
                    'temperature_deviation': readiness_record.get('temperature_deviation', 0),
                    'raw_data': {
                        'activity': activity_data,
                        'sleep': sleep_data,
                        'readiness': readiness_data
                    }
                }
            else:
                return {"error": f"Oura API error: {activity_response.status_code}"}
                
        except Exception as e:
            return {"error": f"Oura sync failed: {str(e)}"}
    
    def sync_apple_health_data(self, access_token: str, date: str = None) -> Dict:
        """Sync data from Apple HealthKit (requires iOS app integration)"""
        # Note: Apple HealthKit requires native iOS app integration
        # This would typically be handled by a companion iOS app that syncs to your backend
        
        return {
            'source': 'Apple Health',
            'note': 'Apple HealthKit requires iOS app integration. Manual data entry supported.',
            'instructions': 'Users can copy/paste Health app summary into daily log for AI analysis.'
        }
    
    def sync_garmin_data(self, access_token: str, access_token_secret: str, date: str = None) -> Dict:
        """Sync data from Garmin Connect IQ API"""
        if not self.garmin_consumer_key:
            return {"error": "Garmin API not configured"}
        
        # Garmin uses OAuth 1.0a, more complex implementation
        try:
            # This is a simplified example - full OAuth 1.0a implementation needed
            return {
                'source': 'Garmin',
                'note': 'Garmin API integration requires OAuth 1.0a setup',
                'status': 'Manual data entry supported - copy from Garmin Connect app'
            }
        except Exception as e:
            return {"error": f"Garmin sync failed: {str(e)}"}
    
    def sync_google_fit_data(self, access_token: str, date: str = None) -> Dict:
        """Sync data from Google Fit API"""
        if not self.google_fit_client_id:
            return {"error": "Google Fit API not configured"}
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Convert date to epoch milliseconds
            start_time = int(datetime.strptime(date, '%Y-%m-%d').timestamp() * 1000)
            end_time = start_time + (24 * 60 * 60 * 1000)  # Add 24 hours
            
            # Get aggregated data
            aggregate_url = 'https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate'
            aggregate_data = {
                "aggregateBy": [
                    {"dataTypeName": "com.google.step_count.delta"},
                    {"dataTypeName": "com.google.calories.expended"},
                    {"dataTypeName": "com.google.active_minutes"},
                    {"dataTypeName": "com.google.heart_rate.bpm"}
                ],
                "bucketByTime": {"durationMillis": 86400000},  # 1 day
                "startTimeMillis": start_time,
                "endTimeMillis": end_time
            }
            
            response = requests.post(aggregate_url, headers=headers, json=aggregate_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract metrics from buckets
                steps = 0
                calories = 0
                active_minutes = 0
                avg_heart_rate = 0
                
                for bucket in data.get('bucket', []):
                    for dataset in bucket.get('dataset', []):
                        data_type = dataset.get('dataSourceId', '')
                        
                        for point in dataset.get('point', []):
                            values = point.get('value', [])
                            if 'step_count' in data_type and values:
                                steps += values[0].get('intVal', 0)
                            elif 'calories' in data_type and values:
                                calories += values[0].get('fpVal', 0)
                            elif 'active_minutes' in data_type and values:
                                active_minutes += values[0].get('intVal', 0)
                            elif 'heart_rate' in data_type and values:
                                avg_heart_rate = values[0].get('fpVal', 0)
                
                return {
                    'source': 'Google Fit',
                    'date': date,
                    'steps': steps,
                    'calories': calories,
                    'active_minutes': active_minutes,
                    'avg_heart_rate': avg_heart_rate,
                    'raw_data': data
                }
            else:
                return {"error": f"Google Fit API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Google Fit sync failed: {str(e)}"}
    
    def sync_all_connected_devices(self, user_tokens: Dict, date: str = None) -> List[Dict]:
        """Sync data from all connected devices for a user"""
        results = []
        
        # Sync Fitbit if token available
        if user_tokens.get('fitbit_access_token'):
            fitbit_data = self.sync_fitbit_data(user_tokens['fitbit_access_token'], date)
            results.append(fitbit_data)
        
        # Sync Oura if token available
        if user_tokens.get('oura_access_token'):
            oura_data = self.sync_oura_data(user_tokens['oura_access_token'], date)
            results.append(oura_data)
        
        # Sync Google Fit if token available
        if user_tokens.get('google_fit_access_token'):
            google_fit_data = self.sync_google_fit_data(user_tokens['google_fit_access_token'], date)
            results.append(google_fit_data)
        
        # Sync Garmin if tokens available
        if user_tokens.get('garmin_access_token') and user_tokens.get('garmin_access_token_secret'):
            garmin_data = self.sync_garmin_data(
                user_tokens['garmin_access_token'], 
                user_tokens['garmin_access_token_secret'], 
                date
            )
            results.append(garmin_data)
        
        return results
    
    # Helper methods for data extraction
    def _extract_fitbit_sleep_hours(self, sleep_data: Dict) -> float:
        """Extract sleep hours from Fitbit sleep data"""
        try:
            sleep_logs = sleep_data.get('sleep', [])
            if sleep_logs:
                main_sleep = sleep_logs[0]  # Primary sleep session
                minutes = main_sleep.get('minutesAsleep', 0)
                return round(minutes / 60, 1)
            return 0
        except:
            return 0
    
    def _extract_fitbit_sleep_score(self, sleep_data: Dict) -> int:
        """Extract sleep score from Fitbit sleep data"""
        try:
            sleep_logs = sleep_data.get('sleep', [])
            if sleep_logs:
                return sleep_logs[0].get('efficiency', 0)
            return 0
        except:
            return 0
    
    def _extract_fitbit_resting_hr(self, hr_data: Dict) -> int:
        """Extract resting heart rate from Fitbit data"""
        try:
            activities_hr = hr_data.get('activities-heart', [])
            if activities_hr:
                return activities_hr[0].get('value', {}).get('restingHeartRate', 0)
            return 0
        except:
            return 0

# Initialize fitness tracker API
fitness_tracker_api = FitnessTrackerAPI()
