
from flask import request, redirect, session, url_for, jsonify
import requests
import base64
import secrets
from urllib.parse import urlencode
import os

class FitnessOAuthHandler:
    """Handle OAuth flows for fitness tracker APIs"""
    
    def __init__(self):
        # OAuth credentials from environment variables
        self.fitbit_client_id = os.getenv('FITBIT_CLIENT_ID')
        self.fitbit_client_secret = os.getenv('FITBIT_CLIENT_SECRET')
        self.oura_client_id = os.getenv('OURA_CLIENT_ID')
        self.oura_client_secret = os.getenv('OURA_CLIENT_SECRET')
        self.google_fit_client_id = os.getenv('GOOGLE_FIT_CLIENT_ID')
        self.google_fit_client_secret = os.getenv('GOOGLE_FIT_CLIENT_SECRET')
        
        # OAuth endpoints
        self.fitbit_auth_url = 'https://www.fitbit.com/oauth2/authorize'
        self.fitbit_token_url = 'https://api.fitbit.com/oauth2/token'
        
        self.oura_auth_url = 'https://cloud.ouraring.com/oauth/authorize'
        self.oura_token_url = 'https://api.ouraring.com/oauth/token'
        
        self.google_auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        self.google_token_url = 'https://oauth2.googleapis.com/token'
    
    def get_fitbit_auth_url(self, user_email: str, base_url: str) -> str:
        """Generate Fitbit OAuth authorization URL"""
        if not self.fitbit_client_id:
            return None
        
        state = secrets.token_urlsafe(32)
        session[f'fitbit_oauth_state_{user_email}'] = state
        
        params = {
            'response_type': 'code',
            'client_id': self.fitbit_client_id,
            'redirect_uri': f"{base_url}/oauth/fitbit/callback",
            'scope': 'activity sleep heartrate profile',
            'state': state
        }
        
        return f"{self.fitbit_auth_url}?{urlencode(params)}"
    
    def get_oura_auth_url(self, user_email: str, base_url: str) -> str:
        """Generate Oura OAuth authorization URL"""
        if not self.oura_client_id:
            return None
        
        state = secrets.token_urlsafe(32)
        session[f'oura_oauth_state_{user_email}'] = state
        
        params = {
            'response_type': 'code',
            'client_id': self.oura_client_id,
            'redirect_uri': f"{base_url}/oauth/oura/callback",
            'scope': 'daily personal',
            'state': state
        }
        
        return f"{self.oura_auth_url}?{urlencode(params)}"
    
    def get_google_fit_auth_url(self, user_email: str, base_url: str) -> str:
        """Generate Google Fit OAuth authorization URL"""
        if not self.google_fit_client_id:
            return None
        
        state = secrets.token_urlsafe(32)
        session[f'google_oauth_state_{user_email}'] = state
        
        params = {
            'response_type': 'code',
            'client_id': self.google_fit_client_id,
            'redirect_uri': f"{base_url}/oauth/google/callback",
            'scope': 'https://www.googleapis.com/auth/fitness.activity.read https://www.googleapis.com/auth/fitness.heart_rate.read https://www.googleapis.com/auth/fitness.sleep.read',
            'state': state,
            'access_type': 'offline'
        }
        
        return f"{self.google_auth_url}?{urlencode(params)}"
    
    def handle_fitbit_callback(self, code: str, state: str, user_email: str, base_url: str) -> dict:
        """Handle Fitbit OAuth callback and exchange code for tokens"""
        # Verify state parameter
        expected_state = session.get(f'fitbit_oauth_state_{user_email}')
        if not expected_state or state != expected_state:
            return {"error": "Invalid state parameter"}
        
        # Exchange code for access token
        auth_string = base64.b64encode(f"{self.fitbit_client_id}:{self.fitbit_client_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': self.fitbit_client_id,
            'grant_type': 'authorization_code',
            'redirect_uri': f"{base_url}/oauth/fitbit/callback",
            'code': code
        }
        
        try:
            response = requests.post(self.fitbit_token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                return {
                    'success': True,
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'expires_in': tokens['expires_in'],
                    'user_id': tokens['user_id']
                }
            else:
                return {"error": f"Token exchange failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Fitbit OAuth failed: {str(e)}"}
    
    def handle_oura_callback(self, code: str, state: str, user_email: str, base_url: str) -> dict:
        """Handle Oura OAuth callback and exchange code for tokens"""
        # Verify state parameter
        expected_state = session.get(f'oura_oauth_state_{user_email}')
        if not expected_state or state != expected_state:
            return {"error": "Invalid state parameter"}
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': self.oura_client_id,
            'client_secret': self.oura_client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': f"{base_url}/oauth/oura/callback",
            'code': code
        }
        
        try:
            response = requests.post(self.oura_token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                return {
                    'success': True,
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'expires_in': tokens['expires_in']
                }
            else:
                return {"error": f"Token exchange failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Oura OAuth failed: {str(e)}"}
    
    def handle_google_fit_callback(self, code: str, state: str, user_email: str, base_url: str) -> dict:
        """Handle Google Fit OAuth callback and exchange code for tokens"""
        # Verify state parameter
        expected_state = session.get(f'google_oauth_state_{user_email}')
        if not expected_state or state != expected_state:
            return {"error": "Invalid state parameter"}
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': self.google_fit_client_id,
            'client_secret': self.google_fit_client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': f"{base_url}/oauth/google/callback",
            'code': code
        }
        
        try:
            response = requests.post(self.google_token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                return {
                    'success': True,
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens.get('refresh_token'),
                    'expires_in': tokens['expires_in']
                }
            else:
                return {"error": f"Token exchange failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Google Fit OAuth failed: {str(e)}"}
    
    def refresh_fitbit_token(self, refresh_token: str) -> dict:
        """Refresh Fitbit access token"""
        auth_string = base64.b64encode(f"{self.fitbit_client_id}:{self.fitbit_client_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        try:
            response = requests.post(self.fitbit_token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Token refresh failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Token refresh failed: {str(e)}"}

# Initialize OAuth handler
oauth_handler = FitnessOAuthHandler()
