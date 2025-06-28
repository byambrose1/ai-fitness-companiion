from flask import Flask, request, render_template_string, jsonify, session, send_from_directory
from datetime import datetime, timedelta
import json
import os
import openai
import stripe
import bcrypt
from data_protection import data_protection
from gdpr_compliance import gdpr_compliance
from database import get_user, save_user, add_daily_log, get_all_users, init_database
from security_monitoring import security_monitor
from email_service import email_service
from food_database import food_db
from food_database import FoodDatabaseAPI, NutritionCalculator

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Admin credentials from environment variables
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'FitnessAdmin2024!')

# Serve static files for PWA
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# PWA offline fallback
@app.route('/offline.html')
def offline():
    return send_from_directory('static', 'offline.html')

# OpenAI setup - you'll need to add your API key via Secrets
openai.api_key = os.getenv('OPENAI_API_KEY', '')

# Stripe setup - you'll need to add your keys via Secrets
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
stripe_publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY', '')

# Initialize database
try:
    init_database()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization failed: {e}")
    print("App will continue with limited functionality")

# Helper function to get users_data for compatibility
def get_users_data():
    """Get all users in dictionary format for compatibility"""
    users = {}
    all_users = get_all_users()
    for email, name, tier in all_users:
        user = get_user(email)
        if user:
            users[email] = user
    return users

# Global variable for compatibility with existing code
users_data = get_users_data()

# Subscription tiers
SUBSCRIPTION_TIERS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'features': ['Basic daily logging', 'Limited AI insights', '7-day data history'],
        'limits': {'daily_logs': 7, 'ai_questions': 3, 'weekly_checkins': 1}
    },
    'premium': {
        'name': 'Premium',
        'price': 997,  # £9.97 in pence
        'stripe_price_id': 'price_premium_monthly',  # You'll set this in Stripe dashboard
        'features': ['Unlimited daily logging', 'Full AI insights', 'Unlimited data history', 'Weekly meal plans', 'Priority support'],
        'limits': {'daily_logs': -1, 'ai_questions': -1, 'weekly_checkins': -1}  # -1 = unlimited
    }
}

@app.route("/register", methods=["POST"])
def register_user():
    """Handle user registration with password"""
    data = request.form
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"success": False, "message": "All fields required"}), 400

    if email in users_data:
        return jsonify({"success": False, "message": "Account already exists"}), 400

    # Hash password securely
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Create user account
    user_data = {
        'name': name,
        'email': email,
        'password': hashed_password.decode('utf-8'),
        'created_at': datetime.now().isoformat(),
        'subscription_tier': 'free',
        'subscription_status': 'active',
        'stripe_customer_id': None,
        'subscription_end_date': None,
        'profile_data': {},
        'daily_logs': [],
        'weekly_checkins': []
    }

    save_user(user_data)
    data_protection.log_data_access(email, "user_registration", request.remote_addr)

    # Send welcome email and add to Mailchimp
    try:
        email_service.send_welcome_email(email, name)
        email_service.add_to_mailchimp(email, name, user_data)
        print(f"✅ Welcome email sent to {email}")
    except Exception as e:
        print(f"⚠️ Email service error: {e}")

    return jsonify({"success": True, "message": "Account created successfully"})

@app.route("/login", methods=["POST"])
def login_user():
    """Handle user login"""
    email = request.form.get("email")
    password = request.form.get("password")
    ip_address = request.remote_addr

    # Log login attempt
    data_protection.log_data_access(email, "login_attempt", ip_address)

    user = get_user(email)
    if not user:
        track_failed_login(email, ip_address)
        return jsonify({"success": False, "message": "Account not found"}), 404

    # Handle legacy passwords (not hashed) and new hashed passwords
    password_valid = False

    try:
        if user['password'].startswith('$2b$') and len(user['password']) > 20:
            # This is a hashed password
            password_valid = bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))
        else:
            # This is a legacy plaintext password
            password_valid = (user['password'] == password)

            if password_valid:
                # Update to hashed password
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                user['password'] = hashed_password.decode('utf-8')
                save_user(user)

    except Exception as e:
        print(f"Password validation error: {e}")
        # Fallback to plaintext comparison for legacy passwords
        password_valid = (user['password'] == password)

        if password_valid:
            # Update to hashed password
            try:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                user['password'] = hashed_password.decode('utf-8')
                save_user(user)
            except Exception as hash_error:
                print(f"Error updating password hash: {hash_error}")

    if not password_valid:
        track_failed_login(email, ip_address)
        return jsonify({"success": False, "message": "Invalid password"}), 401

    # Successful login
    data_protection.log_data_access(email, "login_success", ip_address)
    session['user_email'] = email
    return jsonify({"success": True, "message": "Login successful"})

@app.route("/forgot-password")
def forgot_password_page():
    """Show forgot password form"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en-GB">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Forgot Password - Fitness Companion</title>
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0; padding: 20px;
                background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); 
                min-height: 100vh; display: flex; align-items: center; justify-content: center;
            }
            .container { 
                background: white; padding: 40px; border-radius: 20px; 
                max-width: 500px; width: 100%; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            h1 { color: #3B7A57; text-align: center; margin-bottom: 20px; }
            p { text-align: center; color: #666; margin-bottom: 30px; }
            label { display: block; margin: 15px 0 8px 0; font-weight: 600; color: #3B7A57; }
            input { 
                width: 100%; padding: 16px; border: 2px solid #e5e5e5; 
                border-radius: 12px; font-size: 16px; font-family: 'Inter', sans-serif;
            }
            input:focus { outline: none; border-color: #3B7A57; }
            .button { 
                background: #3B7A57; color: white; padding: 16px 32px; 
                border: none; border-radius: 12px; font-size: 16px; font-weight: 600; 
                cursor: pointer; width: 100%; margin-top: 20px;
            }
            .button:hover { background: #2d5a42; }
            .help-section {
                background: #f8fffe; padding: 20px; border-radius: 12px; margin-top: 30px;
                border-left: 4px solid #A8E6CF;
            }
            .back-link { text-align: center; margin-top: 20px; }
            .back-link a { color: #3B7A57; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Forgot Your Password?</h1>
            <p>No worries! Enter your email address and we'll help you reset your password.</p>

            <form method="POST" action="/send-password-reset">
                <label for="email">Email Address:</label>
                <input type="email" name="email" id="email" placeholder="Enter your email address" required>
                <button type="submit" class="button">📧 Send Reset Link</button>
            </form>

            <div class="help-section">
                <h3 style="margin-top: 0; color: #3B7A57;">🤔 Can't Remember Your Email?</h3>
                <p style="margin-bottom: 15px;">If you can't remember which email you used to sign up:</p>
                <ul style="text-align: left; color: #666;">
                    <li>Check your most commonly used email accounts</li>
                    <li>Search for "Welcome to Your Fitness Journey" in your inbox</li>
                    <li>Look for emails from our fitness app</li>
                    <li>Try signing up again - we'll let you know if an account already exists</li>
                </ul>
                <form method="POST" action="/find-account" style="margin-top: 15px;">
                    <label for="name">Your Name (as registered):</label>
                    <input type="text" name="name" placeholder="Enter your full name" required>
                    <button type="submit" class="button" style="background: #74b9ff;">🔍 Find My Account</button>
                </form>
            </div>

            <div class="back-link">
                <a href="/">← Back to Login</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route("/send-password-reset", methods=["POST"])
def send_password_reset():
    """Send password reset email"""
    email = request.form.get('email')

    if not email:
        return "Email is required", 400

    user = get_user(email)
    if not user:
        # Don't reveal if email exists or not for security
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Password Reset Sent</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; 
                       background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); min-height: 100vh;
                       display: flex; align-items: center; justify-content: center; }
                .container { max-width: 500px; background: white; padding: 40px; border-radius: 15px; }
                .button { background: #3B7A57; color: white; padding: 15px 30px; 
                         text-decoration: none; border-radius: 8px; font-weight: 600; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📧 Check Your Email</h2>
                <p>If an account with that email exists, we've sent password reset instructions.</p>
                <p style="color: #666;">If you don't receive an email within 5 minutes, check your spam folder or try again.</p>
                <a href="/" class="button">← Back to Login</a>
            </div>
        </body>
        </html>
        """)

    # Generate reset token
    import secrets
    reset_token = secrets.token_urlsafe(32)
    reset_expiry = (datetime.now() + timedelta(hours=1)).isoformat()

    # Store reset token in user data
    user['reset_token'] = reset_token
    user['reset_token_expiry'] = reset_expiry
    save_user(user)

    # Send reset email
    try:
        reset_link = f"{request.url_root}reset-password?token={reset_token}"
        email_service.send_password_reset_email(email, user['name'], reset_link)
        message = "Password reset email sent successfully!"
    except Exception as e:
        print(f"Email sending error: {e}")
        message = "Reset link generated. Email service temporarily unavailable."

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Password Reset Sent</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; 
                   background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); min-height: 100vh;
                   display: flex; align-items: center; justify-content: center; }
            .container { max-width: 500px; background: white; padding: 40px; border-radius: 15px; }
            .button { background: #3B7A57; color: white; padding: 15px 30px; 
                     text-decoration: none; border-radius: 8px; font-weight: 600; }
            .reset-link { background: #f8fffe; padding: 15px; border-radius: 8px; 
                         margin: 20px 0; border-left: 4px solid #A8E6CF; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📧 Password Reset Sent!</h2>
            <p>{{ message }}</p>
            {% if reset_link %}
            <div class="reset-link">
                <p><strong>Direct Reset Link:</strong></p>
                <a href="{{ reset_link }}" style="color: #3B7A57;">{{ reset_link }}</a>
            </div>
            {% endif %}
            <p style="color: #666;">This link expires in 1 hour.</p>
            <a href="/" class="button">← Back to Login</a>
        </div>
    </body>
    </html>
    """, message=message, reset_link=reset_link)

@app.route("/find-account", methods=["POST"])
def find_account():
    """Help users find their account by name"""
    name = request.form.get('name')

    if not name:
        return "Name is required", 400

    # Search for users with matching name
    all_users = get_all_users()
    matching_users = []

    for email, user_name, tier in all_users:
        if user_name and name.lower() in user_name.lower():
            # Partially mask email for privacy
            email_parts = email.split('@')
            masked_email = f"{email_parts[0][:2]}***@{email_parts[1]}"
            matching_users.append(masked_email)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Account Search Results</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; 
                   background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); min-height: 100vh;
                   display: flex; align-items: center; justify-content: center; }
            .container { max-width: 500px; background: white; padding: 40px; border-radius: 15px; }
            .button { background: #3B7A57; color: white; padding: 15px 30px; 
                     text-decoration: none; border-radius: 8px; font-weight: 600; margin: 5px; }
            .result { background: #f8fffe; padding: 15px; border-radius: 8px; 
                     margin: 10px 0; border-left: 4px solid #A8E6CF; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔍 Account Search Results</h2>
            {% if matching_users %}
                <p>We found {{ matching_users|length }} account(s) with the name "{{ name }}":</p>
                {% for email in matching_users %}
                <div class="result">{{ email }}</div>
                {% endfor %}
                <p style="color: #666;">Recognize any of these emails? Use them to reset your password.</p>
            {% else %}
                <p>No accounts found with the name "{{ name }}".</p>
                <p style="color: #666;">Try variations of your name or contact support if you need help.</p>
            {% endif %}

            <a href="/forgot-password" class="button">Try Password Reset</a>
            <a href="/" class="button" style="background: #74b9ff;">← Back to Login</a>
        </div>
    </body>
    </html>
    """, matching_users=matching_users, name=name)

@app.route("/reset-password")
def reset_password_form():
    """Show password reset form"""
    token = request.args.get('token')

    if not token:
        return "Invalid reset link", 400

    # Find user with this token
    all_users = get_all_users()
    user = None
    for email, name, tier in all_users:
        user_data = get_user(email)
        if user_data and user_data.get('reset_token') == token:
            # Check if token is expired
            expiry = user_data.get('reset_token_expiry')
            if expiry and datetime.now() < datetime.fromisoformat(expiry):
                user = user_data
                break

    if not user:
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>Invalid Reset Link</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%);">
            <div style="max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px;">
                <h2>🔗 Invalid or Expired Link</h2>
                <p>This password reset link is invalid or has expired.</p>
                <a href="/forgot-password" style="background: #3B7A57; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px;">Request New Reset Link</a>
            </div>
        </body>
        </html>
        """)

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en-GB">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Password</title>
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Inter', sans-serif; margin: 0; padding: 20px;
                background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); 
                min-height: 100vh; display: flex; align-items: center; justify-content: center;
            }
            .container { 
                background: white; padding: 40px; border-radius: 20px; 
                max-width: 500px; width: 100%; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            h1 { color: #3B7A57; text-align: center; margin-bottom: 20px; }
            label { display: block; margin: 15px 0 8px 0; font-weight: 600; color: #3B7A57; }
            input { 
                width: 100%; padding: 16px; border: 2px solid #e5e5e5; 
                border-radius: 12px; font-size: 16px;
            }
            input:focus { outline: none; border-color: #3B7A57; }
            .button { 
                background: #3B7A57; color: white; padding: 16px 32px; 
                border: none; border-radius: 12px; font-size: 16px; font-weight: 600; 
                cursor: pointer; width: 100%; margin-top: 20px;
            }
            .requirements { font-size: 0.8rem; color: #666; margin-top: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Reset Your Password</h1>
            <p style="text-align: center; color: #666;">Enter your new password below</p>

            <form method="POST" action="/update-password">
                <input type="hidden" name="token" value="{{ token }}">

                <label for="password">New Password:</label>
                <input type="password" name="password" id="password" required>
                <div class="requirements">
                    Must contain: 12+ characters, uppercase, lowercase, number, special character
                </div>

                <label for="confirmPassword">Confirm New Password:</label>
                <input type="password" name="confirmPassword" id="confirmPassword" required>

                <button type="submit" class="button">🔄 Update Password</button>
            </form>
        </div>
    </body>
    </html>
    """, token=token)

@app.route("/update-password", methods=["POST"])
def update_password():
    """Update user password from reset"""
    token = request.form.get('token')
    password = request.form.get('password')
    confirm_password = request.form.get('confirmPassword')

    if not token or not password:
        return "Missing required fields", 400

    if password != confirm_password:
        return "Passwords do not match", 400

    # Validate password requirements
    import re
    if len(password) < 12 or not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])', password):
        return "Password does not meet requirements", 400

    # Find user with this token
    all_users = get_all_users()
    user = None
    for email, name, tier in all_users:
        user_data = get_user(email)
        if user_data and user_data.get('reset_token') == token:
            # Check if token is expired
            expiry = user_data.get('reset_token_expiry')
            if expiry and datetime.now() < datetime.fromisoformat(expiry):
                user = user_data
                break

    if not user:
        return "Invalid or expired token", 400

    # Update password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user['password'] = hashed_password.decode('utf-8')

    # Clear reset token
    user.pop('reset_token', None)
    user.pop('reset_token_expiry', None)

    save_user(user)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Password Updated</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; 
                   background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); min-height: 100vh;
                   display: flex; align-items: center; justify-content: center; }
            .container { max-width: 500px; background: white; padding: 40px; border-radius: 15px; }
            .button { background: #3B7A57; color: white; padding: 15px 30px; 
                     text-decoration: none; border-radius: 8px; font-weight: 600; }
            .success-icon { font-size: 3rem; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>
            <h2>Password Updated Successfully!</h2>
            <p>Your password has been reset. You can now log in with your new password.</p>
            <a href="/" class="button">🔑 Login Now</a>
        </div>
    </body>
    </html>
    """)

# Track failed login attempts
failed_attempts = {}
suspicious_ips = set()

# Track failed login attempts
failed_attempts = {}
suspicious_ips = set()

def track_failed_login(email, ip_address):
    """Track failed login attempts for breach detection"""
    key = f"{email}_{ip_address}"
    failed_attempts[key] = failed_attempts.get(key, 0) + 1
    suspicious_ips.add(ip_address)

    # Check for breach indicators
    total_failed = sum(failed_attempts.values())
    breach_detected, alerts = data_protection.detect_breach_indicators(
        total_failed, suspicious_ips
    )

    if breach_detected:
        print(f"⚠️  Breach indicators detected: {alerts}")

@app.route("/questionnaire-complete", methods=["POST"])
def questionnaire_complete():
    """Handle questionnaire completion and prompt for password if needed"""
    data = request.form
    email = data.get("email")

    # Check if user already exists (came from signup flow)
    if email in users_data:
        # User came from signup, just update their profile with questionnaire data
        existing_user = users_data[email]
        existing_user['profile_data'].update(dict(data))
        existing_user['previous_attempts'] = request.form.getlist("previousAttempts")

        # Redirect to success page
        return redirect_to_profile_complete(existing_user)
    else:
        # User came from questionnaire flow, need to create password
        # Store questionnaire data temporarily and show password creation
        questionnaire_data = {
            'form_data': dict(data),
            'previous_attempts': request.form.getlist("previousAttempts"),
            'timestamp': datetime.now().isoformat()
        }

        # Store temporarily (in production, use proper session management)
        session['questionnaire_data'] = questionnaire_data
        session['questionnaire_email'] = email

        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en-GB">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Create Your Password</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
            <style>
                * { box-sizing: border-box; }
                body { 
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 0; padding: 20px;
                    background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); 
                    min-height: 100vh; display: flex; align-items: center; justify-content: center;
                }
                .container { 
                    background: white; padding: 40px; border-radius: 20px; 
                    max-width: 500px; width: 100%; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }
                h1 { color: #3B7A57; text-align: center; margin-bottom: 20px; font-size: 2rem; }
                p { text-align: center; color: #666; margin-bottom: 30px; }
                label { display: block; margin: 15px 0 8px 0; font-weight: 600; color: #3B7A57; }
                input { 
                    width: 100%; padding: 16px; border: 2px solid #e5e5e5; 
                    border-radius: 12px; font-size: 16px; font-family: 'Inter', sans-serif;
                }
                input:focus { outline: none; border-color: #3B7A57; }
                .button { 
                    background: #3B7A57; color: white; padding: 16px 32px; 
                    border: none; border-radius: 12px; font-size: 16px; font-weight: 600; 
                    cursor: pointer; width: 100%; margin-top: 20px;
                }
                .button:hover { background: #2d5a42; }
                .success-icon { font-size: 3rem; text-align: center; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">🎉</div>
                <h1>Almost There!</h1>
                <p>Your questionnaire is complete. Create a password to finish setting up your account and access your personalized dashboard.</p>

                <form method="POST" action="/complete-signup">
                    <label for="password">Create Your Password:</label>
                    <input type="password" name="password" id="password" placeholder="Minimum 6 characters" required>

                    <label for="confirmPassword">Confirm Password:</label>
                    <input type="password" name="confirmPassword" id="confirmPassword" placeholder="Re-enter your password" required>

                    <button type="submit" class="button">🚀 Complete Setup & Go to Dashboard</button>
                </form>
            </div>
        </body>
        </html>
        """)

@app.route("/complete-signup", methods=["POST"])
def complete_signup():
    """Complete signup after questionnaire for password-less users"""
    password = request.form.get('password')
    confirm_password = request.form.get('confirmPassword')

    if not password or len(password) < 6:
        return "Password must be at least 6 characters", 400

    if password != confirm_password:
        return "Passwords do not match", 400

    # Get questionnaire data from session
    questionnaire_data = session.get('questionnaire_data')
    email = session.get('questionnaire_email')

    if not questionnaire_data or not email:
        return "Session expired. Please start over.", 400

    # Calculate age from stored form data
    dob = questionnaire_data['form_data'].get("dob")
    if dob:
        birth_date = datetime.strptime(dob, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    else:
        age = "Not provided"

    # Hash password securely
    import bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Create user profile
    user_profile = {
        'name': questionnaire_data['form_data'].get("name"),
        'email': email,
        'password': hashed_password.decode('utf-8'),
        'dob': dob,
        'age': age,
        'created_at': datetime.now().isoformat(),
        'subscription_tier': 'free',
        'subscription_status': 'active',
        'profile_data': questionnaire_data['form_data'],
        'previous_attempts': questionnaire_data['previous_attempts'],
        'daily_logs': [],
        'weekly_checkins': []
    }

    # Save user to database
    save_user(user_profile)
    
    # Add to users_data dictionary for immediate availability
    users_data[email] = user_profile

    # Clear session data
    session.pop('questionnaire_data', None)
    session.pop('questionnaire_email', None)

    return redirect_to_profile_complete(user_profile)

def redirect_to_profile_complete(user_profile):
    """Generate the profile complete page"""
    data = user_profile['profile_data']
    previous_attempts = user_profile.get('previous_attempts', [])

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Setup Complete!</title>
        <style>
            body { 
                font-family: 'Inter', sans-serif; text-align: center; padding: 20px; 
                background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); min-height: 100vh;
                display: flex; align-items: center; justify-content: center;
            }
            .container { 
                max-width: 600px; margin: 0 auto; background: white; 
                padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            .success-icon { font-size: 4rem; margin-bottom: 20px; }
            h1 { color: #3B7A57; margin-bottom: 20px; font-size: 2.5rem; }
            .message { color: #666; font-size: 1.2rem; margin-bottom: 30px; }
            .button { 
                background: #3B7A57; color: white; padding: 16px 32px; 
                text-decoration: none; border-radius: 12px; font-weight: 600; 
                font-size: 1.1rem; display: inline-block; margin: 10px;
            }
            .button:hover { background: #2d5a42; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">🎉</div>
            <h1>Welcome to Your Fitness Journey!</h1>
            <p class="message">Your account has been created successfully and your personalized profile is ready. Let's start building healthy habits together!</p>

            <a href="/dashboard?email={{ email }}" class="button">🏠 Go to Your Dashboard</a>
            <a href="/daily-log?email={{ email }}" class="button">📝 Start Daily Log</a>
        </div>
    </body>
    </html>
    """, email=user_profile['email'])

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        # This now redirects to questionnaire_complete for processing
        return questionnaire_complete()

        # Extract all form data for display
        gender = data.get("gender")
        height = data.get("height")
        weight = data.get("weight")
        goal_weight = data.get("goalWeight")
        goal = data.get("goal")
        goal_reason = data.get("goalReason")
        motivation = data.get("motivation")
        mental_state = data.get("mentalState")
        motivation_level = data.get("motivationLevel")
        mood = data.get("mood")
        mood_custom = data.get("moodCustom")
        medications = data.get("medications")
        medication_list = data.get("medicationList")
        health_conditions = data.get("healthConditions")
        menstrual_cycle = data.get("menstrualCycle")
        sleep_hours = data.get("sleepHours")
        waking_feeling = data.get("wakingFeeling")
        protein_sources = data.get("proteinSources")
        meals_per_day = data.get("mealsPerDay")
        water_intake = data.get("waterIntake")
        eating_habits = data.get("eatingHabits")
        activity_level = data.get("activityLevel")
        exercise_details = data.get("exerciseDetails")
        wearables = data.get("wearables")
        weight_changes = data.get("weightChanges")
        body_feeling = data.get("bodyFeeling")
        weekly_weigh_in = data.get("weeklyWeighIn")
        stress_level = data.get("stressLevel")
        support_system = data.get("supportSystem")
        support_explanation = data.get("supportExplanation")
        ai_consent = data.get("aiConsent")

        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en-GB">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>✨ Your Personalised Fitness Profile</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
            <style>
                * { box-sizing: border-box; }

                body { 
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 0; padding: 20px;
                    background: #ffffff;
                    min-height: 100vh;
                    color: #1a1a1a;
                }

                .container {
                    background: white; padding: 2em; border-radius: 20px;
                    max-width: 900px; margin: 0 auto;
                    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                }

                .summary-item { 
                    margin: 12px 0; padding: 15px; 
                    background: linear-gradient(145deg, #f8fffe, #e6f9f2);
                    border-radius: 12px; border-left: 5px solid #A8E6CF;
                    transition: transform 0.2s ease;
                }

                .summary-item:hover { transform: translateY(-2px); }

                .button { 
                    display: inline-block; padding: 15px 30px; 
                    background: linear-gradient(135deg, #A8E6CF, #7ED3B2);
                    color: #2d5a3d; text-decoration: none; border-radius: 12px; 
                    margin: 10px 5px; text-align: center; font-weight: 600;
                    transition: all 0.3s ease; border: none; cursor: pointer;
                    font-size: 16px;
                }

                .button:hover { 
                    transform: translateY(-3px);
                    box-shadow: 0 8px 25px rgba(168, 230, 207, 0.4);
                }

                .button.secondary {
                    background: linear-gradient(135deg, #6c7b7f, #495c61);
                    color: white;
                }

                h1 { 
                    text-align: center; color: #2d5a3d; margin-bottom: 30px;
                    font-size: 2.5rem; font-weight: 700;
                }

                h2 { 
                    color: #2d5a3d; margin-top: 30px; 
                    border-bottom: 3px solid #A8E6CF; padding-bottom: 10px;
                    font-size: 1.5rem;
                }

                .ai-section {
                    background: linear-gradient(145deg, #e3f9e5, #c8f2cc);
                    padding: 25px; border-radius: 15px; margin: 25px 0;
                    text-align: center; border-left: 5px solid #7ED3B2;
                }

                .highlight {
                    background: linear-gradient(145deg, #fff9e6, #ffeaa7);
                    border-left-color: #fdcb6e;
                }

                .next-steps {
                    background: linear-gradient(145deg, #f0f8ff, #e6f3ff);
                    padding: 25px; border-radius: 15px; margin: 30px 0;
                    border-left: 5px solid #74b9ff;
                }

                .feature-grid {
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px; margin: 20px 0;
                }

                .feature-card {
                    background: white; padding: 20px; border-radius: 12px;
                    border-left: 4px solid #A8E6CF; text-align: center;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                }

                @media (max-width: 768px) {
                    .container { padding: 1.5em; margin: 0.5em; }
                    h1 { font-size: 2rem; }
                    .feature-grid { grid-template-columns: 1fr; }
                }

                .success-badge {
                    display: inline-block; background: #00b894; color: white;
                    padding: 8px 16px; border-radius: 20px; font-size: 14px;
                    font-weight: 600; margin: 5px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✨ Your Fat Loss Journey Starts Here</h1>
                <div style="text-align: center; margin-bottom: 30px;">
                    <span class="success-badge">✅ Profile Created Successfully</span>
                </div>

                <p style="text-align: center; font-size: 18px; color: #2d5a3d; margin-bottom: 30px;">
                    Thank you for sharing your information, {{ name|title }}! Your personalised wellness companion is ready.
                </p>

                <h2>👤 Your Profile Summary</h2>
                <div class="summary-item"><strong>Email:</strong> {{ email }}</div>
                <div class="summary-item"><strong>Age:</strong> {{ age }} years old</div>
                <div class="summary-item"><strong>Sex assigned at birth:</strong> {{ gender|title }}</div>
                <div class="summary-item"><strong>Height:</strong> {{ height }} cm</div>
                <div class="summary-item"><strong>Current Weight:</strong> {{ weight }} kg</div>
                {% if goal_weight %}
                <div class="summary-item"><strong>Goal Weight:</strong> {{ goal_weight }} kg</div>
                {% endif %}

                <h2>🎯 Your Wellness Goals</h2>
                <div class="summary-item highlight"><strong>Primary Goal:</strong> {{ goal|replace('_', ' ')|title }}</div>
                {% if goal_reason %}
                <div class="summary-item"><strong>Motivation:</strong> {{ goal_reason|replace('_', ' ')|title }}</div>
                {% endif %}
                <div class="summary-item"><strong>Your Why:</strong> {{ motivation }}</div>

                <h2>💭 Current State</h2>
                <div class="summary-item"><strong>Mental State:</strong> {{ mental_state }}</div>
                <div class="summary-item"><strong>Motivation Level:</strong> {{ motivation_level }}/10</div>
                <div class="summary-item"><strong>Stress Level:</strong> {{ stress_level }}/10</div>
                <div class="summary-item"><strong>Sleep:</strong> {{ sleep_hours }} hours (feeling {{ waking_feeling|lower }})</div>

                {% if ai_consent == 'yes' %}
                <div class="ai-section">
                    <h2>🤖 Your AI-Powered Insights</h2>
                    <p><strong>Based on your profile, here are your personalised recommendations:</strong></p>

                    <div style="text-align: left; margin: 20px 0;">
                        <div class="summary-item">
                            <strong>🎯 Goal-Specific Guidance:</strong> 
                            {% if goal == 'fat_loss' %}
                                Focus on sustainable habits rather than quick fixes. With {{ sleep_hours }} hours of sleep and stress at {{ stress_level }}/10, prioritising recovery will support your fat loss goals.
                            {% elif goal == 'muscle_gain' %}
                                Consistency with protein intake and progressive training will be key. Your {{ activity_level|replace('_', ' ') }} activity level provides a solid foundation.
                            {% elif goal == 'general_health' %}
                                Small, consistent improvements in nutrition and movement will compound over time. Focus on building sustainable habits.
                            {% else %}
                                Regular movement and stress management techniques will significantly benefit your mental wellbeing journey.
                            {% endif %}
                        </div>

                        <div class="summary-item">
                            <strong>🧠 Wellbeing Focus:</strong>
                            {% if stress_level|int > 6 %}
                                Your stress levels suggest prioritising stress management techniques. Consider meditation, walks, or other relaxation methods alongside your fitness goals.
                            {% elif motivation_level|int < 5 %}
                                Building momentum with small wins will help increase motivation. Start with achievable daily goals.
                            {% else %}
                                You're in a good headspace to pursue your goals. Use this positive energy to establish consistent routines.
                            {% endif %}
                        </div>

                        {% if menstrual_cycle and menstrual_cycle != '' %}
                        <div class="summary-item">
                            <strong>🌙 Cycle-Aware Tips:</strong>
                            Your menstrual cycle affects energy, appetite, and recovery. We'll help you adjust expectations and strategies throughout your cycle for better results.
                        </div>
                        {% endif %}
                    </div>
                </div>
                {% endif %}

                <div class="next-steps">
                    <h2>🚀 What's Next?</h2>
                    <p style="margin-bottom: 20px;">Your fitness companion is now set up! Here's what you can look forward to:</p>

                    <div class="feature-grid">
                        <div class="feature-card">
                            <h3>📝 Daily Logging</h3>
                            <p>Track food, exercise, mood, and sleep with our intelligent system</p>
                        </div>
                        <div class="feature-card">
                            <h3>🤖 AI Feedback</h3>
                            <p>Get personalised insights based on your data and goals</p>
                        </div>
                        <div class="feature-card">
                            <h3>📊 Progress Tracking</h3>
                            <p>Monitor your journey with smart analytics and trends</p>
                        </div>
                        <div class="feature-card">
                            <h3>🔔 Gentle Reminders</h3>
                            <p>Stay on track with supportive, non-judgmental prompts</p>
                        </div>
                    </div>

                    <p style="text-align: center; margin-top: 25px; font-style: italic; color: #666;">
                        💚 Remember: This is about progress, not perfection. Small consistent steps lead to lasting change.
                    </p>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="/dashboard?email={{ email }}" class="button">🏠 Go to Dashboard</a>
                    <a href="/daily-log?email={{ email }}" class="button">📝 Start Daily Log</a>
                    <a href="/" class="button secondary">↺ Update Profile</a>
                </div>
            </div>
        </body>
        </html>
        """, 
        name=name, email=email, age=age, gender=gender, height=height, weight=weight, 
        goal_weight=goal_weight, goal=goal, goal_reason=goal_reason, motivation=motivation,
        mental_state=mental_state, motivation_level=motivation_level, mood=mood, 
        mood_custom=mood_custom, medications=medications, medication_list=medication_list,
        health_conditions=health_conditions, menstrual_cycle=menstrual_cycle,
        sleep_hours=sleep_hours, waking_feeling=waking_feeling, protein_sources=protein_sources,
        meals_per_day=meals_per_day, water_intake=water_intake, eating_habits=eating_habits,
        activity_level=activity_level, exercise_details=exercise_details, wearables=wearables,
        weight_changes=weight_changes, body_feeling=body_feeling, weekly_weigh_in=weekly_weigh_in,
        stress_level=stress_level, support_system=support_system, support_explanation=support_explanation,
        ai_consent=ai_consent)

    return open("templates/index.html").read()

@app.route("/dashboard")
def dashboard():
    email = request.args.get('email')
    if not email:
        return "Please provide email parameter"

    # Get user from database (refresh users_data if needed)
    user = get_user(email)
    if not user:
        return "User not found. Please complete your profile first."
    
    # Update users_data dictionary
    users_data[email] = user

    # Check if user has completed questionnaire
    if not user.get('profile_data'):
        return "Please complete your questionnaire first. <a href='/'>Start here</a>"

    # Calculate streak and contextual messaging
    daily_logs = user.get('daily_logs', [])
    streak_days = 1
    total_logs = len(daily_logs)

    if daily_logs:
        # Calculate actual streak based on recent days
        recent_dates = set()
        for log in daily_logs[-7:]:  # Last 7 logs
            if 'date' in log:
                recent_dates.add(log['date'])
        streak_days = len(recent_dates)

    signup_date = datetime.strptime(user['created_at'], "%Y-%m-%dT%H:%M:%S.%f")
    days_since_signup = (datetime.now() - signup_date).days

    # Enhanced contextual messaging based on user behavior
    if days_since_signup == 0:
        contextual_message = "🌟 Welcome! Starting a new journey takes courage, and you've already taken the first step. Let's build healthy habits together."
    elif days_since_signup <= 3:
        if total_logs >= 2:
            contextual_message = f"💪 Amazing start! {total_logs} logs in {days_since_signup + 1} days. You're building momentum!"
        else:
            contextual_message = "🌱 Every expert was once a beginner. Take it one day at a time - you've got this!"
    elif days_since_signup <= 7:
        if streak_days >= 5:
            contextual_message = f"🔥 Incredible! {streak_days}-day streak shows real commitment. Consistency is your superpower!"
        else:
            contextual_message = "💚 Remember: progress isn't about being perfect, it's about not giving up. Every log matters!"
    elif total_logs >= 15:
        contextual_message = f"🏆 Outstanding dedication! {total_logs} logs show you're serious about your health journey."
    else:
        contextual_message = "🌟 Your journey is unique and valuable. Focus on progress, not perfection - you're doing better than you think!"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en-GB">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Wellness Dashboard</title>
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px;
                background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); min-height: 100vh;
            }
            .container { background: white; padding: 2em; border-radius: 20px; max-width: 1000px; margin: 0 auto; }
            .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
            .card { background: #f8fffe; padding: 20px; border-radius: 15px; border-left: 5px solid #A8E6CF; }
            .score { font-size: 2rem; font-weight: bold; color: #2d5a3d; }
            .button { 
                display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #A8E6CF, #7ED3B2);
                color: #2d5a3d; text-decoration: none; border-radius: 8px; margin: 5px; font-weight: 600;
            }
            .reminder { background: #e3f9e5; padding: 15px; border-radius: 10px; margin: 15px 0; text-align: center; }
            h1 { color: #2d5a3d; text-align: center; }
            h2 { color: #2d5a3d; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌟 Welcome back, {{ user.name|title }}!</h1>

            <div class="reminder">
                <p>💚 <strong>Daily Motivation:</strong> {{ contextual_message }}</p>
            </div>

            <!-- Streak and Progress Section -->
            <div class="card" style="background: linear-gradient(135deg, #A8E6CF, #D1F2EB); text-align: center; margin-bottom: 20px;">
                <h3 style="color: #1a1a1a;">🔥 Your Progress</h3>
                <div style="display: flex; justify-content: space-around; align-items: center;">
                    <div>
                        <div style="font-size: 2.5rem; font-weight: 700; color: #3B7A57;">{{ streak_days }}</div>
                        <div style="font-size: 0.9rem; color: #2d5a42;">Day Streak</div>
                    </div>
                    <div>
                        <div style="font-size: 2.5rem; font-weight: 700; color: #3B7A57;">{{ total_logs }}</div>
                        <div style="font-size: 0.9rem; color: #2d5a42;">Total Logs</div>
                    </div>
                    <div>
                        <div style="font-size: 2.5rem; font-weight: 700; color: #3B7A57;">{{ days_since_signup + 1 }}</div>
                        <div style="font-size: 0.9rem; color: #2d5a42;">Days Active</div>
                    </div>
                </div>
            </div>

            <div class="dashboard-grid">
                <div class="card">
                    <h3>📊 Quick Score</h3>
                    {% if recent_score %}
                        <div class="score">{{ recent_score }}/10</div>
                        <p>Based on your latest entries</p>
                    {% else %}
                        <div class="score">Ready!</div>
                        <p>Complete your daily log to see your score</p>
                    {% endif %}
                </div>

                <div class="card">
                    <h3>🎯 Your Goal</h3>
                    <p><strong>{{ user.profile_data.goal|replace('_', ' ')|title }}</strong></p>
                    <p>{{ user.profile_data.motivation[:100] }}...</p>
                </div>

                <div class="card">
                    <h3>💭 Quick Stats</h3>
                    <p><strong>Motivation:</strong> {{ user.profile_data.motivationLevel }}/10</p>
                    <p><strong>Stress:</strong> {{ user.profile_data.stressLevel }}/10</p>
                    <p><strong>Sleep:</strong> {{ user.profile_data.sleepHours }} hours</p>
                </div>

                {% if user.profile_data.menstrualCycle %}
                <div class="card">
                    <h3>🌙 Cycle Status</h3>
                    <p>{{ user.profile_data.menstrualCycle|replace('_', ' ')|title }}</p>
                    <p><small>Adjusting recommendations based on your cycle phase</small></p>
                </div>
                {% endif %}
            </div>

            <h2>🚀 Quick Actions</h2>
            <div class="card">
                <h3>💳 Subscription Status</h3>
                <p><strong>Plan:</strong> {{ user.subscription_tier|title }} 
                {% if user.subscription_tier == 'free' %}
                    <a href="/subscription?email={{ user.email }}" style="color: #7ED3B2; font-weight: bold;">Upgrade →</a>
                {% endif %}
                </p>
                {% if user.subscription_tier == 'free' %}
                <p><small>Limited to 3 AI questions per week, 7-day history</small></p>
                {% else %}
                <p><small>✨ Unlimited access to all features</small></p>
                {% endif %}
            </div>

            <div style="text-align: center;">
                <a href="/daily-log?email={{ user.email }}" class="button">📝 Daily Log</a>
                <a href="/weekly-checkin?email={{ user.email }}" class="button">📅 Weekly Check-in</a>
                <a href="/ai-chat?email={{ user.email }}" class="button">🤖 Ask AI</a>
                <a href="/subscription?email={{ user.email }}" class="button">💳 Subscription</a>
                <a href="/" class="button">⚙️ Update Profile</a>
            </div>
        </div>
    </body>
    </html>
    """, user=user, contextual_message=contextual_message, streak_days=streak_days, 
         total_logs=total_logs, days_since_signup=days_since_signup, recent_score=None)

@app.route("/daily-log")
def daily_log():
    email = request.args.get('email')
    if not email:
        return "Please provide email parameter"

    # Get user for smart suggestions
    user = get_user(email) if email in users_data else None
    streak_days = 1
    predicted_breakfast = "Oats with berries"
    predicted_workout = "30min walk"
    habit_anchor = "have my morning coffee"

    # Generate contextual message based on user state
    contextual_messages = [
        "Starting a new journey takes courage, and you've already taken the first step.",
        "Consistency beats perfection. Just log what you can!",
        "Every small step counts toward your bigger goal.",
        "Your body is learning from every choice you make.",
        "Progress isn't always linear, but it's always valuable."
    ]

    if user:
        # Calculate streak
        daily_logs = user.get('daily_logs', [])
        if daily_logs:
            # Simple streak calculation
            recent_dates = set()
            for log in daily_logs[-7:]:  # Last 7 logs
                if 'date' in log:
                    recent_dates.add(log['date'])
            streak_days = len(recent_dates)

        # Smart predictions based on recent logs
        if daily_logs:
            recent_foods = []
            recent_workouts = []
            for log in daily_logs[-5:]:  # Last 5 logs
                if log.get('food_log'):
                    recent_foods.append(log['food_log'])
                if log.get('workout'):
                    recent_workouts.append(log['workout'])

            # Extract common breakfast items
            if recent_foods:
                breakfast_items = []
                for food in recent_foods:
                    if 'breakfast' in food.lower():
                        breakfast_items.append(food.split('breakfast')[1].split(',')[0].strip())
                if breakfast_items:
                    predicted_breakfast = breakfast_items[-1]  # Most recent

            # Predict workout
            if recent_workouts:
                workout_counts = {}
                for workout in recent_workouts:
                    workout_counts[workout] = workout_counts.get(workout, 0) + 1
                predicted_workout = max(workout_counts, key=workout_counts.get)

    contextual_message = contextual_messages[streak_days % len(contextual_messages)]

    return open("templates/daily-log.html").read().replace("{{ email }}", email)\
                                                .replace("{{ today }}", datetime.now().strftime("%Y-%m-%d"))\
                                                .replace("{{ streak_days or 1 }}", str(streak_days))\
                                                .replace("{{ predicted_breakfast or \"Oats with berries\" }}", predicted_breakfast)\
                                                .replace("{{ predicted_workout or \"30min walk\" }}", predicted_workout)\
                                                .replace("{{ habit_anchor or 'have my morning coffee' }}", habit_anchor)\
                                                .replace("{{ contextual_message }}", contextual_message)

@app.route("/save-daily-log", methods=["POST"])
def save_daily_log():
    email = request.form.get('email')
    if email not in users_data:
        return "User not found"

    # Save the daily log entry
    log_entry = {
        'date': request.form.get('date'),
        'timestamp': datetime.now().isoformat(),
        'food_log': request.form.get('food_log'),
        'workout': request.form.get('workout'),
        'workout_duration': request.form.get('workout_duration'),
        'weight': request.form.get('weight'),
        'mood': request.form.get('mood'),
        'sleep_hours': request.form.get('sleep_hours'),
        'stress_level': request.form.get('stress_level'),
        'water_intake': request.form.get('water_intake'),
        'tracking_devices': request.form.get('tracking_devices'),
        'notes': request.form.get('notes')
    }

    users_data[email]['daily_logs'].append(log_entry)
    add_daily_log(email, log_entry)

    # Calculate instant feedback score
    score = 4.0  # Base score
    insights = []

    # Mood scoring
    mood_scores = {'excellent': 2, 'good': 1.5, 'okay': 0.5, 'low': 0}
    if log_entry.get('mood') in mood_scores:
        score += mood_scores[log_entry['mood']]
        if log_entry['mood'] == 'excellent':
            insights.append("Your excellent mood shows you're in a great headspace! 😊")
        elif log_entry['mood'] == 'good':
            insights.append("Good mood = good choices ahead! 👍")
        elif log_entry['mood'] == 'okay':
            insights.append("Every day doesn't have to be perfect! 💚")

    # Water intake scoring
    water_scores = {'excellent': 1.5, 'good': 1, 'moderate': 0.5, 'low': 0}
    if log_entry.get('water_intake') in water_scores:
        score += water_scores[log_entry['water_intake']]
        if log_entry['water_intake'] in ['excellent', 'good']:
            insights.append("Great hydration supports your metabolism! 💧")

    # Workout scoring
    if log_entry.get('workout') and log_entry['workout'] != 'rest':
        score += 1.5
        insights.append("Movement is medicine for both body and mind! 💪")
    elif log_entry.get('workout') == 'rest':
        score += 0.5
        insights.append("Rest days are crucial for recovery - well done! 😴")

    # Sleep scoring
    if log_entry.get('sleep_hours'):
        try:
            sleep = float(log_entry['sleep_hours'])
            if 7 <= sleep <= 9:
                score += 1.5
                insights.append("Optimal sleep supports hormone balance! 🌙")
            elif sleep >= 6:
                score += 1
                insights.append("Good sleep foundation! 🌙")
        except:
            pass

    # Food logging bonus
    if log_entry.get('food_log') and len(log_entry['food_log']) > 10:
        score += 1
        insights.append("Tracking your food helps identify patterns! 📝")

    # Stress level scoring
    if log_entry.get('stress_level'):
        try:
            stress = int(log_entry['stress_level'])
            if stress <= 3:
                score += 0.5
                insights.append("Low stress levels support your goals! 🧘‍♀️")
            elif stress >= 8:
                insights.append("High stress noted - consider relaxation techniques 🌸")
        except:
            pass

    # Notes bonus - AI processing indicator
    if log_entry.get('notes') and len(log_entry['notes']) > 5:
        score += 0.5
        insights.append("📝 Your notes have been analyzed by AI for personalized insights!")

    # Tracking devices bonus
    if log_entry.get('tracking_devices') and len(log_entry['tracking_devices']) > 10:
        score += 0.5
        insights.append("📱 Device data integrated for better health tracking!")

    # Generate personalized insight
    user = users_data[email]
    daily_logs = user.get('daily_logs', [])
    streak_days = len(set(log.get('date') for log in daily_logs if log.get('date')))

    if streak_days >= 7:
        insights.append(f"🔥 Amazing! {streak_days} days of consistent logging!")
    elif streak_days >= 3:
        insights.append(f"💚 Great streak! {streak_days} days and counting!")

    # Cap score at 10
    final_score = min(10.0, score)

    # Select best insights (max 2)
    selected_insights = insights[:2] if len(insights) > 2 else insights
    insight_text = " ".join(selected_insights) if selected_insights else "Every log helps us understand your patterns better! 🤖"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Daily Log Saved - Instant Insights!</title>
        <style>
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
                text-align: center; padding: 20px; 
                background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); 
                min-height: 100vh; display: flex; align-items: center; justify-content: center;
            }
            .container { 
                max-width: 600px; margin: 0 auto; background: white; 
                padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            .celebration { font-size: 4rem; margin-bottom: 20px; animation: bounce 1s ease-in-out; }
            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-30px); }
                60% { transform: translateY(-15px); }
            }
            .score-circle {
                width: 120px; height: 120px; border-radius: 50%;
                background: linear-gradient(135deg, #3B7A57, #A8E6CF);
                display: flex; align-items: center; justify-content: center;
                margin: 20px auto; color: white; font-size: 2rem; font-weight: 700;
                box-shadow: 0 10px 30px rgba(59, 122, 87, 0.3);
            }
            .insights {
                background: #e3f9e5; padding: 20px; border-radius: 12px; margin: 20px 0;
                border-left: 5px solid #7ED3B2; text-align: left;
            }
            .insights h3 { margin: 0 0 12px 0; color: #3B7A57; }
            .insights p { margin: 0; color: #2d5a42; line-height: 1.5; }
            .button { 
                background: linear-gradient(135deg, #3B7A57, #2d5a42); color: white; 
                padding: 15px 30px; text-decoration: none; border-radius: 12px; 
                font-weight: 600; display: inline-block; margin: 10px;
                transition: all 0.2s ease;
            }
            .button:hover { 
                transform: translateY(-2px); 
                box-shadow: 0 8px 25px rgba(59, 122, 87, 0.3);
            }
            .streak-badge {
                background: #fdcb6e; color: #8b7000; padding: 8px 16px;
                border-radius: 20px; font-size: 14px; font-weight: 600;
                display: inline-block; margin: 10px 0;
            }
            h1 { color: #3B7A57; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="celebration">🎉</div>
            <h1>Daily Log Saved Successfully!</h1>

            <div class="score-circle">{{ "%.1f"|format(final_score) }}/10</div>

            <div class="streak-badge">🔥 Day {{ streak_days }} Streak</div>

            <div class="insights">
                <h3>🤖 Your Instant Insights</h3>
                <p>{{ insight_text }}</p>
            </div>

            <p style="color: #666; margin: 20px 0;">
                Consistency beats perfection! Every log helps us understand your patterns and provide better guidance.
            </p>

            <a href="/dashboard?email={{ email }}" class="button">🏠 Back to Dashboard</a>
            <a href="/daily-log?email={{ email }}" class="button" style="background: linear-gradient(135deg, #74b9ff, #0984e3);">📝 Log Tomorrow</a>
        </div>
    </body>
    </html>
    """, email=email, final_score=final_score, insight_text=insight_text, streak_days=streak_days)

@app.route("/subscription")
def subscription_page():
    email = request.args.get('email')
    if not email or email not in users_data:
        return "User not found"

    user = users_data[email]
    current_tier = user.get('subscription_tier', 'free')

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en-GB">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Subscription Plans</title>
        <script src="https://js.stripe.com/v3/"></script>
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px;
                background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); min-height: 100vh;
            }
            .container { background: white; padding: 2em; border-radius: 20px; max-width: 900px; margin: 0 auto; }
            .plans-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin: 30px 0; }
            .plan-card { 
                background: white; border-radius: 15px; padding: 30px; text-align: center;
                border: 3px solid #e0e0e0; transition: all 0.3s ease;
            }
            .plan-card.current { border-color: #A8E6CF; background: #f8fffe; }
            .plan-card.premium { border-color: #7ED3B2; }
            .plan-card:hover { transform: translateY(-5px); }
            .price { font-size: 2.5rem; font-weight: bold; color: #2d5a3d; margin: 15px 0; }
            .features { list-style: none; padding: 0; margin: 20px 0; }
            .features li { padding: 8px 0; border-bottom: 1px solid #eee; }
            .features li:before { content: "✅ "; color: #00b894; }
            .button { 
                display: inline-block; padding: 15px 30px; 
                background: linear-gradient(135deg, #A8E6CF, #7ED3B2);
                color: #2d5a3d; text-decoration: none; border-radius: 12px; 
                font-weight: 600; cursor: pointer; border: none; font-size: 16px;
                transition: all 0.3s ease; width: 100%;
            }
            .button:hover { transform: translateY(-2px); }
            .button:disabled { opacity: 0.5; cursor: not-allowed; }
            .current-badge { 
                background: #00b894; color: white; padding: 5px 15px; 
                border-radius: 20px; font-size: 12px; margin-bottom: 10px;
            }
            h1 { color: #2d5a3d; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💳 Choose Your Plan</h1>
            <p style="text-align: center; color: #666; margin-bottom: 30px;">
                Unlock the full potential of your fitness journey
            </p>

            <div class="plans-grid">
                <div class="plan-card {% if current_tier == 'free' %}current{% endif %}">
                    {% if current_tier == 'free' %}
                    <div class="current-badge">Current Plan</div>
                    {% endif %}
                    <h2>🆓 Free</h2>
                    <div class="price">£0<span style="font-size: 1rem;">/month</span></div>
                    <ul class="features">
                        <li>Basic daily logging</li>
                        <li>Limited AI insights (3/week)</li>
                        <li>7-day data history</li>
                        <li>1 weekly check-in</li>
                    </ul>
                    {% if current_tier != 'free' %}
                    <form method="POST" action="/downgrade">
                        <input type="hidden" name="email" value="{{ email }}">
                        <button type="submit" class="button">Downgrade to Free</button>
                    </form>
                    {% else %}
                    <button class="button" disabled>Current Plan</button>
                    {% endif %}
                </div>

                <div class="plan-card premium {% if current_tier == 'premium' %}current{% endif %}">
                    {% if current_tier == 'premium' %}
                    <div class="current-badge">Current Plan</div>
                    {% endif %}
                    <h2>✨ Premium</h2>
                    <div class="price">£9.97<span style="font-size: 1rem;">/month</span></div>
                    <ul class="features">
                        <li>Unlimited daily logging</li>
                        <li>Full AI insights & chat</li>
                        <li>Unlimited data history</li>
                        <li>Weekly meal plans</li>
                        <li>Priority support</li>
                        <li>Advanced analytics</li>
                    </ul>
                    {% if current_tier != 'premium' %}
                    <button onclick="createCheckoutSession('{{ email }}')" class="button">Upgrade to Premium</button>
                    {% else %}
                    <button class="button" disabled>Current Plan</button>
                    {% endif %}
                </div>
            </div>

            <div style="text-align: center; margin-top: 30px;">
                <a href="/dashboard?email={{ email }}" style="color: #2d5a3d;">← Back to Dashboard</a>
            </div>
        </div>

        <script>
            const stripe = Stripe('{{ stripe_publishable_key }}');

            async function createCheckoutSession(email) {
                const response = await fetch('/create-checkout-session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `email=${email}`
                });

                const session = await response.json();

                if (session.error) {
                    alert('Error: ' + session.error);
                    return;
                }

                // Redirect to Stripe Checkout
                const result = await stripe.redirectToCheckout({
                    sessionId: session.id
                });

                if (result.error) {
                    alert(result.error.message);
                }
            }
        </script>
    </body>
    </html>
    """, email=email, current_tier=current_tier, stripe_publishable_key=stripe_publishable_key)

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    email = request.form.get('email')

    if not email or email not in users_data:
        return jsonify({'error': 'User not found'}), 404

    if not stripe.api_key:
        return jsonify({'error': 'Stripe not configured'}), 500

    try:
        user = users_data[email]

        # Create or get Stripe customer
        if not user.get('stripe_customer_id'):
            customer = stripe.Customer.create(
                email=email,
                name=user['name']
            )
            users_data[email]['stripe_customer_id'] = customer.id
        else:
            customer_id = user['stripe_customer_id']

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=user.get('stripe_customer_id'),
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': 'Fitness Companion Premium',
                        'description': 'Unlimited AI insights, meal plans, and advanced features'
                    },
                    'unit_amount': SUBSCRIPTION_TIERS['premium']['price'],
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.url_root + 'subscription-success?session_id={CHECKOUT_SESSION_ID}&email=' + email,
            cancel_url=request.url_root + 'subscription?email=' + email,
        )

        return jsonify({'id': session.id})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route("/subscription-success")
def subscription_success():
    session_id = request.args.get('session_id')
    email = request.args.get('email')

    if not session_id or not email:
        return "Missing parameters"

    try:
        # Retrieve the session
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            # Update user subscription
            if email in users_data:
                users_data[email]['subscription_tier'] = 'premium'
                users_data[email]['subscription_status'] = 'active'
                users_data[email]['subscription_end_date'] = None  # Will be managed by Stripe

        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Subscription Success</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; }
                .success { color: #00b894; font-size: 24px; margin: 20px 0; }
            .button { background: #A8E6CF; color: #2d5a3d; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; }
        </style>
        </head>
        <body>
            <div class="container">
                <h1>🎉 Welcome to Premium!</h1>
                <div class="success">✅ Subscription activated successfully</div>
                <p>You now have access to all premium features including unlimited AI insights, meal plans, and advanced analytics.</p>
                <a href="/dashboard?email={{ email }}" class="button">Go to Dashboard</a>
            </div>
        </body>
        </html>
        """, email=email)

    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/downgrade", methods=["POST"])
def downgrade_subscription():
    email = request.form.get('email')

    if not email or email not in users_data:
        return "User not found"

    # Update user to free tier
    users_data[email]['subscription_tier'] = 'free'
    users_data[email]['subscription_status'] = 'active'

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Downgraded to Free</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; }
            .button { background: #A8E6CF; color: #2d5a3d; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📱 Downgraded to Free Plan</h2>
            <p>You've been moved to the free plan. You can upgrade anytime!</p>
            <a href="/dashboard?email={{ email }}" class="button">Go to Dashboard</a>
        </div>
    </body>
    </html>
    """, email=email)

def check_subscription_limits(email, action_type):
    """Check if user has reached their subscription limits"""
    if email not in users_data:
        return False

    user = users_data[email]
    tier = user.get('subscription_tier', 'free')
    limits = SUBSCRIPTION_TIERS[tier]['limits']

    if limits.get(action_type, 0) == -1:  # Unlimited
        return True

    # Count current usage
    if action_type == 'daily_logs':
        current_count = len(user['daily_logs'])
    elif action_type == 'weekly_checkins':
        current_count = len(user['weekly_checkins'])
    elif action_type == 'ai_questions':
        # Count AI questions from today
        today = datetime.now().strftime("%Y-%m-%d")
        current_count = sum(1 for log in user.get('ai_logs', []) if log.get('date') == today)
    else:
        return True

    return current_count < limits.get(action_type, 0)

@app.route("/weekly-checkin")
def weekly_checkin():
    email = request.args.get('email')
    if not email:
        return "Please provide email parameter"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en-GB">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weekly Check-in</title>
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px;
                background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); min-height: 100vh;
            }
            .container { background: white; padding: 2em; border-radius: 20px; max-width: 600px; margin: 0 auto; }
            input, textarea, select { 
                width: 100%; padding: 12px; margin: 8px 0; border: 2px solid #A8E6CF; 
                border-radius: 8px; font-size: 16px;
            }
            label { display: block; margin-top: 15px; font-weight: 600; color: #2d5a3d; }
            .button { 
                background: linear-gradient(135deg, #A8E6CF, #7ED3B2); color: #2d5a3d; 
                padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; 
                font-weight: 600; cursor: pointer; width: 100%; margin-top: 20px;
            }
            h1 { color: #2d5a3d; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📅 Weekly Check-in</h1>
            <p style="text-align: center; color: #666;">Reflect on your week and get AI-powered feedback</p>

            <form method="POST" action="/save-weekly-checkin">
                <input type="hidden" name="email" value="{{ email }}">
                <input type="hidden" name="week_of" value="{{ today }}">

                <label for="adherence">📊 How well did you follow your plan this week? (1-10):</label>
                <input type="range" name="adherence" min="1" max="10" value="5" oninput="document.getElementById('adherence-value').textContent = this.value">
                <span id="adherence-value">5</span>/10

                <label for="energy">⚡ Average energy level this week:</label>
                <select name="energy">
                    <option value="very_low">Very Low</option>
                    <option value="low">Low</option>
                    <option value="moderate">Moderate</option>
                    <option value="high">High</option>
                    <option value="very_high">Very High</option>
                </select>

                <label for="bloating">🫃 Bloating/digestive issues:</label>
                <select name="bloating">
                    <option value="none">None</option>
                    <option value="mild">Mild</option>
                    <option value="moderate">Moderate</option>
                    <option value="severe">Severe</option>
                </select>

                <label for="hunger">🍽️ Hunger levels:</label>
                <select name="hunger">
                    <option value="very_low">Very Low</option>
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="very_high">Very High</option>
                </select>

                <label for="weight_change">⚖️ Weight difference from last week (optional):</label>
                <input type="number" name="weight_change" step="0.1" placeholder="e.g., -0.5 or +1.2">

                <label for="challenges">🤔 What were your biggest challenges this week?</label>
                <textarea name="challenges" placeholder="E.g., busy schedule, stress eating, lack of motivation..." rows="3"></textarea>

                <label for="wins">🎉 What went well this week?</label>
                <textarea name="wins" placeholder="E.g., consistent workouts, better sleep, healthy meal prep..." rows="3"></textarea>

                <label for="focus_next_week">🎯 What do you want to focus on next week?</label>
                <textarea name="focus_next_week" placeholder="E.g., increase water intake, try new recipes, prioritize sleep..." rows="2"></textarea>

                <button type="submit" class="button">💾 Submit Check-in & Get AI Feedback</button>
            </form>

            <div style="text-align: center; margin-top: 20px;">
                <a href="/dashboard?email={{ email }}" style="color: #2d5a3d;">← Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """, email=email, today=datetime.now().strftime("%Y-%m-%d"))

@app.route("/save-weekly-checkin", methods=["POST"])
def save_weekly_checkin():
    email = request.form.get('email')
    if email not in users_data:
        return "User not found"

    # Save the weekly check-in
    checkin_data = {
        'week_of': request.form.get('week_of'),
        'timestamp': datetime.now().isoformat(),
        'adherence': request.form.get('adherence'),
        'energy': request.form.get('energy'),
        'bloating': request.form.get('bloating'),
        'hunger': request.form.get('hunger'),
        'weight_change': request.form.get('weight_change'),
        'challenges': request.form.get('challenges'),
        'wins': request.form.get('wins'),
        'focus_next_week': request.form.get('focus_next_week')
    }

    users_data[email]['weekly_checkins'].append(checkin_data)

    # Generate AI feedback if OpenAI key is available
    ai_feedback = "AI feedback temporarily unavailable. Please ensure OpenAI API key is configured."

    if openai.api_key:
        try:
            user_profile = users_data[email]['profile_data']
            prompt = f"""
            Based on this user's weekly check-in and profile, provide supportive, educational feedback:

            User Profile: {user_profile.get('goal')} goal, stress level {user_profile.get('stressLevel')}/10
            Weekly Check-in: Adherence {checkin_data['adherence']}/10, Energy: {checkin_data['energy']}
            Challenges: {checkin_data['challenges']}
            Wins: {checkin_data['wins']}

            Provide 3-4 sentences of encouraging, specific advice focusing on sustainable habits.
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            ai_feedback = response.choices[0].message.content
        except Exception as e:
            ai_feedback = f"AI feedback unavailable: {str(e)}"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Weekly Check-in Complete</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; }
            .ai-feedback { background: #e3f9e5; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #7ED3B2; }
            .button { background: #A8E6CF; color: #2d5a3d; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>✅ Weekly Check-in Complete!</h2>

            <div class="ai-feedback">
                <h3>🤖 Your Personalized AI Feedback</h3>
                <p>{{ ai_feedback }}</p>
            </div>

            <p>Keep up the great work! Your consistency and self-reflection are key to long-term success.</p>
            <a href="/dashboard?email={{ email }}" class="button">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """, email=email, ai_feedback=ai_feedback)

@app.route("/ai-chat")
def ai_chat():
    email = request.args.get('email')
    if not email:
        return "Please provide email parameter"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en-GB">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Wellness Assistant</title>
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px;
                background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); min-height: 100vh;
            }
            .container { background: white; padding: 2em; border-radius: 20px; max-width: 700px; margin: 0 auto; }
            .chat-input { width: 100%; padding: 15px; border: 2px solid #A8E6CF; border-radius: 10px; font-size: 16px; }
            .button { 
                background: linear-gradient(135deg, #A8E6CF, #7ED3B2); color: #2d5a3d; 
                padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; 
                font-weight: 600; cursor: pointer; margin-top: 10px;
            }
            .suggested-questions { margin: 20px 0; }
            .question-btn { 
                background: #f0f8ff; border: 2px solid #A8E6CF; padding: 10px 15px; 
                margin: 5px; border-radius: 20px; cursor: pointer; display: inline-block;
                font-size: 14px; color: #2d5a3d;
            }
            .question-btn:hover { background: #A8E6CF; }
            h1 { color: #2d5a3d; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Wellness Assistant</h1>
            <p style="text-align: center; color: #666;">Ask me anything about your fitness journey!</p>

            <form method="POST" action="/ai-response">
                <input type="hidden" name="email" value="{{ email }}">
                <textarea name="question" class="chat-input" rows="4" placeholder="E.g., Why didn't I lose weight this week? Why do I feel bloated today? What should I improve?"></textarea>
                <button type="submit" class="button">💬 Ask AI Assistant</button>
            </form>

            <div class="suggested-questions">
                <h3>💡 Suggested Questions:</h3>
                <div class="question-btn" onclick="document.querySelector('[name=question]').value = 'Why didn\\'t I lose weight this week?'">Why didn't I lose weight this week?</div>
                <div class="question-btn" onclick="document.querySelector('[name=question]').value = 'Why do I feel bloated today?'">Why do I feel bloated today?</div>
                <div class="question-btn" onclick="document.querySelector('[name=question]').value = 'What should I focus on next week?'">What should I focus on next week?</div>
                <div class="question-btn" onclick="document.querySelector('[name=question]').value = 'How can I improve my energy levels?'">How can I improve my energy levels?</div>
                <div class="question-btn" onclick="document.querySelector('[name=question]').value = 'Tips for better sleep?'">Tips for better sleep?</div>
            </div>

            <div style="text-align: center; margin-top: 20px;">
                <a href="/dashboard?email={{ email }}" style="color: #2d5a3d;">← Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """, email=email)

@app.route("/ai-response", methods=["POST"])
def ai_response():
    email = request.form.get('email')
    question = request.form.get('question')

    if email not in users_data:
        return "User not found"

    # Check subscription limits
    if not check_subscription_limits(email, 'ai_questions'):
        user = users_data[email]
        tier = user.get('subscription_tier', 'free')
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Subscription Limit Reached</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; text-align: center; }
            .limit-warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 10px; margin: 20px 0; }
            .button { background: #A8E6CF; color: #2d5a3d; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 5px; }
            .upgrade-btn { background: linear-gradient(135deg, #7ED3B2, #A8E6CF); }
        </style>
        </head>
        <body>
            <div class="container">
                <h2>🔒 AI Question Limit Reached</h2>
                <div class="limit-warning">
                    <p>You've reached your {{ tier }} plan limit for AI questions this week.</p>
                    <p><strong>Free Plan:</strong> 3 AI questions per week</p>
                    <p><strong>Premium Plan:</strong> Unlimited AI questions</p>
                </div>
                <a href="/subscription?email={{ email }}" class="button upgrade-btn">✨ Upgrade to Premium</a>
                <a href="/dashboard?email={{ email }}" class="button">← Back to Dashboard</a>
            </div>
        </body>
        </html>
        """, email=email, tier=tier)

    # Generate AI response if OpenAI key is available```python
    ai_response = "AI assistant temporarily unavailable. Please ensure OpenAI API key is configured in Secrets."

    if openai.api_key:
        try:
            user_data = users_data[email]
            user_profile = user_data['profile_data']
            recent_logs = user_data['daily_logs'][-7:] if user_data['daily_logs'] else []

            # Extract notes and tracking device data from recent logs
            recent_notes = []
            tracking_data = []
            for log in recent_logs:
                if log.get('notes'):
                    recent_notes.append(f"Day {log.get('date', 'unknown')}: {log['notes']}")
                if log.get('tracking_devices'):
                    tracking_data.append(f"Day {log.get('date', 'unknown')}: {log['tracking_devices']}")

            context = f"""
            You are a supportive, knowledgeable fitness and wellness coach. Answer the user's question based on their profile and recent data.

            User Profile: {user_profile.get('goal')} goal, {user_profile.get('gender')} {user_profile.get('age')} years old
            Sleep: {user_profile.get('sleepHours')} hours, Stress: {user_profile.get('stressLevel')}/10
            Motivation: {user_profile.get('motivationLevel')}/10
            Menstrual cycle: {user_profile.get('menstrualCycle', 'N/A')}

            Recent daily logs (last 7 days): {recent_logs}

            Recent notes from user: {recent_notes if recent_notes else 'None'}
            Tracking device data: {tracking_data if tracking_data else 'None'}

            User Question: {question}

            Provide a supportive, educational response in 3-4 sentences. Be specific and actionable. Reference their notes and tracking data when relevant.
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": context}],
                max_tokens=300
            )
            ai_response = response.choices[0].message.content
        except Exception as e:
            ai_response = f"AI assistant error: {str(e)}"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Response</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); }
            .container { max-width: 700px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; }
            .question { background: #f0f8ff; padding: 15px; border-radius: 10px; margin: 15px 0; border-left: 5px solid #74b9ff; }
            .response { background: #e3f9e5; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #7ED3B2; }
            .button { background: #A8E6CF; color: #2d5a3d; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🤖 AI Wellness Assistant Response</h2>

            <div class="question">
                <strong>Your Question:</strong><br>
                {{ question }}
            </div>

            <div class="response">
                <strong>🤖 AI Response:</strong><br>
                {{ ai_response }}
            </div>

            <div style="text-align: center;">
                <a href="/ai-chat?email={{ email }}" class="button">💬 Ask Another Question</a>
                <a href="/dashboard?email={{ email }}" class="button">🏠 Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """, email=email, question=question, ai_response=ai_response)

@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            data_protection.log_data_access('admin', "admin_login", request.remote_addr)
        else:
            return "Invalid credentials", 401

    if not session.get('admin_authenticated'):
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Login</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
                .login-container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 400px; width: 100%; }
                h2 { color: #3B7A57; text-align: center; margin-bottom: 30px; }
                input { width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
                button { width: 100%; padding: 12px; background: #3B7A57; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
                button:hover { background: #2d5a42; }
            </style>
        </head>
        <body>
            <div class="login-container">
                <h2>🔐 Admin Access</h2>
                <form method="POST">
                    <input type="text" name="username" placeholder="Admin Username" required>
                    <input type="password" name="password" placeholder="Admin Password" required>
                    <button type="submit">Access Dashboard</button>
                </form>
            </div>
        </body>
        </html>
        """)

    # Get detailed user information
    users = get_all_users()
    detailed_users = []
    
    for email, name, tier in users:
        user_data = get_user(email)
        if user_data:
            # Calculate user stats
            daily_logs_count = len(user_data.get('daily_logs', []))
            weekly_checkins_count = len(user_data.get('weekly_checkins', []))
            join_date = user_data.get('created_at', 'Unknown')
            
            # Parse join date for better display
            try:
                from datetime import datetime
                if join_date != 'Unknown':
                    parsed_date = datetime.fromisoformat(join_date.replace('Z', '+00:00'))
                    join_date_display = parsed_date.strftime('%d %b %Y')
                    days_since_join = (datetime.now() - parsed_date).days
                else:
                    join_date_display = 'Unknown'
                    days_since_join = 0
            except:
                join_date_display = 'Unknown'
                days_since_join = 0
            
            # Get goal from profile data
            goal = user_data.get('profile_data', {}).get('goal', 'Not specified')
            motivation = user_data.get('profile_data', {}).get('motivation', '')[:100] + '...' if user_data.get('profile_data', {}).get('motivation', '') else 'Not provided'
            
            detailed_users.append({
                'email': email,
                'name': name,
                'tier': tier,
                'join_date': join_date_display,
                'days_since_join': days_since_join,
                'daily_logs': daily_logs_count,
                'weekly_checkins': weekly_checkins_count,
                'goal': goal.replace('_', ' ').title(),
                'motivation': motivation,
                'stripe_customer_id': user_data.get('stripe_customer_id', 'None'),
                'subscription_status': user_data.get('subscription_status', 'Unknown')
            })
    
    # Sort by join date (newest first)
    detailed_users.sort(key=lambda x: x['days_since_join'])

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard - User Management</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }
            .header { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
            .stat-card { background: #3B7A57; color: white; padding: 20px; border-radius: 8px; text-align: center; }
            .stat-number { font-size: 2rem; font-weight: bold; }
            .stat-label { font-size: 0.9rem; opacity: 0.9; }
            .search-bar { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; margin: 10px 0; }
            .users-table { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .table-header { background: #3B7A57; color: white; padding: 15px; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 120px; gap: 15px; font-weight: bold; }
            .user-row { padding: 15px; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 120px; gap: 15px; border-bottom: 1px solid #eee; cursor: pointer; transition: background 0.2s; }
            .user-row:hover { background: #f8f9fa; }
            .user-row:last-child { border-bottom: none; }
            .tier-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; text-align: center; }
            .tier-free { background: #e3f2fd; color: #1976d2; }
            .tier-premium { background: #fff3e0; color: #f57c00; }
            .user-name { font-weight: bold; color: #333; }
            .user-email { color: #666; font-size: 0.9rem; }
            .user-goal { color: #555; font-size: 0.9rem; }
            .actions { display: flex; gap: 8px; }
            .btn { padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.8rem; text-decoration: none; color: white; }
            .btn-edit { background: #2196f3; }
            .btn-upgrade { background: #ff9800; }
            .btn-view { background: #4caf50; }
            .quick-actions { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .quick-actions a { display: inline-block; padding: 10px 15px; margin: 5px; background: #3B7A57; color: white; text-decoration: none; border-radius: 6px; }
            .quick-actions a:hover { background: #2d5a42; }
            .empty-state { text-align: center; padding: 40px; color: #666; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ Admin Dashboard</h1>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{{ detailed_users|length }}</div>
                    <div class="stat-label">Total Users</div>
                </div>
                <div class="stat-card" style="background: #ff9800;">
                    <div class="stat-number">{{ detailed_users|selectattr('tier', 'equalto', 'premium')|list|length }}</div>
                    <div class="stat-label">Premium Users</div>
                </div>
                <div class="stat-card" style="background: #2196f3;">
                    <div class="stat-number">{{ detailed_users|selectattr('tier', 'equalto', 'free')|list|length }}</div>
                    <div class="stat-label">Free Users</div>
                </div>
                <div class="stat-card" style="background: #4caf50;">
                    <div class="stat-number">{{ detailed_users|map(attribute='daily_logs')|sum }}</div>
                    <div class="stat-label">Total Logs</div>
                </div>
            </div>
        </div>

        <div class="quick-actions">
            <h3>Quick Actions</h3>
            <a href="/admin/export">📊 Export Data</a>
            <a href="/admin/data-retention">📅 Data Retention</a>
            <a href="/admin/backup">💾 Create Backup</a>
            <a href="/admin/logout">🚪 Logout</a>
        </div>

        <div class="users-table">
            <div class="table-header">
                <div>User Details</div>
                <div>Joined</div>
                <div>Subscription</div>
                <div>Goal</div>
                <div>Activity</div>
                <div>Status</div>
                <div>Actions</div>
            </div>

            <input type="text" class="search-bar" placeholder="🔍 Search users by name, email, or goal..." onkeyup="filterUsers(this.value)">

            {% if detailed_users %}
                {% for user in detailed_users %}
                <div class="user-row" onclick="viewUserDetails('{{ user.email }}')">
                    <div>
                        <div class="user-name">{{ user.name }}</div>
                        <div class="user-email">{{ user.email }}</div>
                        <div class="user-goal">{{ user.goal }}</div>
                    </div>
                    <div>
                        <div>{{ user.join_date }}</div>
                        <div style="font-size: 0.8rem; color: #666;">{{ user.days_since_join }} days ago</div>
                    </div>
                    <div>
                        <div class="tier-badge tier-{{ user.tier }}">{{ user.tier|title }}</div>
                        {% if user.stripe_customer_id != 'None' %}
                        <div style="font-size: 0.8rem; color: #666;">Stripe: ✓</div>
                        {% endif %}
                    </div>
                    <div>{{ user.goal }}</div>
                    <div>
                        <div>📝 {{ user.daily_logs }} logs</div>
                        <div>📅 {{ user.weekly_checkins }} check-ins</div>
                    </div>
                    <div>{{ user.subscription_status|title }}</div>
                    <div class="actions" onclick="event.stopPropagation();">
                        <a href="/admin/user/{{ user.email }}" class="btn btn-view">View</a>
                        {% if user.tier == 'free' %}
                        <a href="/admin/upgrade/{{ user.email }}" class="btn btn-upgrade">Upgrade</a>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <h3>No users found</h3>
                    <p>Users will appear here once they sign up</p>
                </div>
            {% endif %}
        </div>

        <script>
            function filterUsers(searchTerm) {
                const rows = document.querySelectorAll('.user-row');
                const lowerSearch = searchTerm.toLowerCase();
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    if (text.includes(lowerSearch)) {
                        row.style.display = 'grid';
                    } else {
                        row.style.display = 'none';
                    }
                });
            }

            function viewUserDetails(email) {
                window.location.href = `/admin/user/${encodeURIComponent(email)}`;
            }
        </script>
    </body>
    </html>
    """, detailed_users=detailed_users)

@app.route("/admin/user/<email>")
def admin_user_details(email):
    if not session.get('admin_authenticated'):
        return "Access denied", 403

    user = get_user(email)
    if not user:
        return f"User {email} not found", 404

    # Calculate user statistics
    daily_logs = user.get('daily_logs', [])
    weekly_checkins = user.get('weekly_checkins', [])
    profile_data = user.get('profile_data', {})
    
    # Get recent activity
    recent_logs = daily_logs[-10:] if daily_logs else []
    
    # Parse join date
    try:
        from datetime import datetime
        join_date = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
        join_date_display = join_date.strftime('%d %B %Y at %H:%M')
        days_since_join = (datetime.now() - join_date).days
    except:
        join_date_display = user.get('created_at', 'Unknown')
        days_since_join = 0

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>User Details - {{ user.name }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .user-info { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
            .info-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .info-card h3 { margin-top: 0; color: #3B7A57; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }
            .stat-card { background: #3B7A57; color: white; padding: 15px; border-radius: 8px; text-align: center; }
            .stat-number { font-size: 1.5rem; font-weight: bold; }
            .stat-label { font-size: 0.8rem; opacity: 0.9; }
            .tier-badge { padding: 6px 15px; border-radius: 20px; font-weight: bold; display: inline-block; }
            .tier-free { background: #e3f2fd; color: #1976d2; }
            .tier-premium { background: #fff3e0; color: #f57c00; }
            .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; color: white; margin: 5px; display: inline-block; }
            .btn-primary { background: #3B7A57; }
            .btn-warning { background: #ff9800; }
            .btn-danger { background: #f44336; }
            .btn-secondary { background: #6c757d; }
            .logs-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            .logs-table th, .logs-table td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            .logs-table th { background: #f8f9fa; }
            .back-link { color: #3B7A57; text-decoration: none; font-weight: bold; }
            .back-link:hover { text-decoration: underline; }
            .action-buttons { margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/admin" class="back-link">← Back to Admin Dashboard</a>
                <h1>👤 {{ user.name }}</h1>
                <p style="color: #666; margin: 5px 0;">{{ user.email }}</p>
                <div class="tier-badge tier-{{ user.subscription_tier }}">{{ user.subscription_tier|title }} Plan</div>
                
                <div class="action-buttons">
                    {% if user.subscription_tier == 'free' %}
                    <a href="/admin/upgrade-user/{{ user.email }}" class="btn btn-warning">⬆️ Upgrade to Premium</a>
                    {% else %}
                    <a href="/admin/downgrade-user/{{ user.email }}" class="btn btn-secondary">⬇️ Downgrade to Free</a>
                    {% endif %}
                    <a href="/admin/edit-user/{{ user.email }}" class="btn btn-primary">✏️ Edit User</a>
                    <a href="/admin/delete-user/{{ user.email }}" class="btn btn-danger" onclick="return confirm('Are you sure you want to delete this user?')">🗑️ Delete User</a>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{{ days_since_join }}</div>
                    <div class="stat-label">Days Since Join</div>
                </div>
                <div class="stat-card" style="background: #2196f3;">
                    <div class="stat-number">{{ daily_logs|length }}</div>
                    <div class="stat-label">Daily Logs</div>
                </div>
                <div class="stat-card" style="background: #4caf50;">
                    <div class="stat-number">{{ weekly_checkins|length }}</div>
                    <div class="stat-label">Weekly Check-ins</div>
                </div>
                <div class="stat-card" style="background: #ff9800;">
                    <div class="stat-number">{{ user.subscription_status|title }}</div>
                    <div class="stat-label">Account Status</div>
                </div>
            </div>

            <div class="user-info">
                <div class="info-card">
                    <h3>📋 Account Information</h3>
                    <p><strong>Email:</strong> {{ user.email }}</p>
                    <p><strong>Name:</strong> {{ user.name }}</p>
                    <p><strong>Joined:</strong> {{ join_date_display }}</p>
                    <p><strong>Subscription:</strong> {{ user.subscription_tier|title }}</p>
                    <p><strong>Status:</strong> {{ user.subscription_status|title }}</p>
                    {% if user.stripe_customer_id %}
                    <p><strong>Stripe Customer:</strong> {{ user.stripe_customer_id }}</p>
                    {% else %}
                    <p><strong>Stripe Customer:</strong> Not connected</p>
                    {% endif %}
                </div>

                <div class="info-card">
                    <h3>🎯 Profile & Goals</h3>
                    {% if profile_data %}
                    <p><strong>Goal:</strong> {{ profile_data.get('goal', 'Not specified')|replace('_', ' ')|title }}</p>
                    <p><strong>Age:</strong> {{ profile_data.get('age', 'Not provided') }}</p>
                    <p><strong>Gender:</strong> {{ profile_data.get('gender', 'Not specified')|title }}</p>
                    <p><strong>Height:</strong> {{ profile_data.get('height', 'Not provided') }} cm</p>
                    <p><strong>Weight:</strong> {{ profile_data.get('weight', 'Not provided') }} kg</p>
                    <p><strong>Activity Level:</strong> {{ profile_data.get('activityLevel', 'Not specified')|replace('_', ' ')|title }}</p>
                    <p><strong>Sleep Hours:</strong> {{ profile_data.get('sleepHours', 'Not provided') }}</p>
                    <p><strong>Stress Level:</strong> {{ profile_data.get('stressLevel', 'Not provided') }}/10</p>
                    {% else %}
                    <p>Profile not completed</p>
                    {% endif %}
                </div>
            </div>

            {% if profile_data.get('motivation') %}
            <div class="info-card">
                <h3>💭 User's Motivation</h3>
                <p>"{{ profile_data.motivation }}"</p>
            </div>
            {% endif %}

            <div class="info-card">
                <h3>📊 Recent Activity</h3>
                {% if recent_logs %}
                <table class="logs-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Weight</th>
                            <th>Mood</th>
                            <th>Sleep</th>
                            <th>Workout</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for log in recent_logs %}
                        <tr>
                            <td>{{ log.get('date', 'N/A') }}</td>
                            <td>{{ log.get('weight', 'N/A') }} kg</td>
                            <td>{{ log.get('mood', 'N/A')|title }}</td>
                            <td>{{ log.get('sleep_hours', 'N/A') }}h</td>
                            <td>{{ log.get('workout', 'N/A') }}</td>
                            <td>{{ (log.get('notes', '') or 'No notes')[:50] }}{% if log.get('notes', '') and log.get('notes')|length > 50 %}...{% endif %}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <p>No daily logs yet</p>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    """, user=user, daily_logs=daily_logs, weekly_checkins=weekly_checkins, 
         profile_data=profile_data, recent_logs=recent_logs, 
         join_date_display=join_date_display, days_since_join=days_since_join)

@app.route("/admin/upgrade-user/<email>", methods=["GET", "POST"])
def admin_upgrade_user(email):
    if not session.get('admin_authenticated'):
        return "Access denied", 403

    user = get_user(email)
    if not user:
        return "User not found", 404

    if request.method == "POST":
        # Upgrade user to premium
        user['subscription_tier'] = 'premium'
        user['subscription_status'] = 'active'
        save_user(user)
        
        data_protection.log_data_access(email, "admin_upgrade", request.remote_addr)
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>User Upgraded</title></head>
        <body style="font-family: Arial; padding: 20px; text-align: center;">
            <h2>✅ User Upgraded Successfully</h2>
            <p>{{ email }} has been upgraded to Premium</p>
            <a href="/admin/user/{{ email }}" style="color: #3B7A57;">← Back to User Details</a>
        </body>
        </html>
        """, email=email)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head><title>Upgrade User</title></head>
    <body style="font-family: Arial; padding: 20px; text-align: center;">
        <h2>⬆️ Upgrade User to Premium</h2>
        <p>Are you sure you want to upgrade <strong>{{ email }}</strong> to Premium?</p>
        <form method="POST" style="margin: 20px 0;">
            <button type="submit" style="background: #3B7A57; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer;">Yes, Upgrade</button>
            <a href="/admin/user/{{ email }}" style="background: #6c757d; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin-left: 10px;">Cancel</a>
        </form>
    </body>
    </html>
    """, email=email)

@app.route("/admin/downgrade-user/<email>", methods=["GET", "POST"])
def admin_downgrade_user(email):
    if not session.get('admin_authenticated'):
        return "Access denied", 403

    user = get_user(email)
    if not user:
        return "User not found", 404

    if request.method == "POST":
        # Downgrade user to free
        user['subscription_tier'] = 'free'
        user['subscription_status'] = 'active'
        save_user(user)
        
        data_protection.log_data_access(email, "admin_downgrade", request.remote_addr)
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>User Downgraded</title></head>
        <body style="font-family: Arial; padding: 20px; text-align: center;">
            <h2>⬇️ User Downgraded Successfully</h2>
            <p>{{ email }} has been downgraded to Free</p>
            <a href="/admin/user/{{ email }}" style="color: #3B7A57;">← Back to User Details</a>
        </body>
        </html>
        """, email=email)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head><title>Downgrade User</title></head>
    <body style="font-family: Arial; padding: 20px; text-align: center;">
        <h2>⬇️ Downgrade User to Free</h2>
        <p>Are you sure you want to downgrade <strong>{{ email }}</strong> to Free?</p>
        <form method="POST" style="margin: 20px 0;">
            <button type="submit" style="background: #f44336; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer;">Yes, Downgrade</button>
            <a href="/admin/user/{{ email }}" style="background: #6c757d; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin-left: 10px;">Cancel</a>
        </form>
    </body>
    </html>
    """, email=email)

@app.route("/admin/edit-user/<email>", methods=["GET", "POST"])
def admin_edit_user(email):
    if not session.get('admin_authenticated'):
        return "Access denied", 403

    user = get_user(email)
    if not user:
        return "User not found", 404

    if request.method == "POST":
        # Update user details
        user['name'] = request.form.get('name', user['name'])
        user['subscription_tier'] = request.form.get('subscription_tier', user['subscription_tier'])
        user['subscription_status'] = request.form.get('subscription_status', user['subscription_status'])
        
        # Update profile data if provided
        profile_data = user.get('profile_data', {})
        if request.form.get('goal'):
            profile_data['goal'] = request.form.get('goal')
        if request.form.get('height'):
            profile_data['height'] = request.form.get('height')
        if request.form.get('weight'):
            profile_data['weight'] = request.form.get('weight')
        
        user['profile_data'] = profile_data
        save_user(user)
        
        data_protection.log_data_access(email, "admin_edit", request.remote_addr)
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>User Updated</title></head>
        <body style="font-family: Arial; padding: 20px; text-align: center;">
            <h2>✅ User Updated Successfully</h2>
            <p>{{ email }} has been updated</p>
            <a href="/admin/user/{{ email }}" style="color: #3B7A57;">← Back to User Details</a>
        </body>
        </html>
        """, email=email)

    profile_data = user.get('profile_data', {})
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit User - {{ user.name }}</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; margin: 5px; }
            .btn-primary { background: #3B7A57; color: white; }
            .btn-secondary { background: #6c757d; color: white; text-decoration: none; display: inline-block; }
        </style>
    </head>
    <body>
        <h1>✏️ Edit User: {{ user.name }}</h1>
        
        <form method="POST">
            <div class="form-group">
                <label for="name">Name:</label>
                <input type="text" name="name" id="name" value="{{ user.name }}" required>
            </div>
            
            <div class="form-group">
                <label for="subscription_tier">Subscription Tier:</label>
                <select name="subscription_tier" id="subscription_tier">
                    <option value="free" {% if user.subscription_tier == 'free' %}selected{% endif %}>Free</option>
                    <option value="premium" {% if user.subscription_tier == 'premium' %}selected{% endif %}>Premium</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="subscription_status">Subscription Status:</label>
                <select name="subscription_status" id="subscription_status">
                    <option value="active" {% if user.subscription_status == 'active' %}selected{% endif %}>Active</option>
                    <option value="cancelled" {% if user.subscription_status == 'cancelled' %}selected{% endif %}>Cancelled</option>
                    <option value="suspended" {% if user.subscription_status == 'suspended' %}selected{% endif %}>Suspended</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="goal">Goal:</label>
                <select name="goal" id="goal">
                    <option value="fat_loss" {% if profile_data.get('goal') == 'fat_loss' %}selected{% endif %}>Fat Loss</option>
                    <option value="muscle_gain" {% if profile_data.get('goal') == 'muscle_gain' %}selected{% endif %}>Muscle Gain</option>
                    <option value="general_health" {% if profile_data.get('goal') == 'general_health' %}selected{% endif %}>General Health</option>
                    <option value="maintenance" {% if profile_data.get('goal') == 'maintenance' %}selected{% endif %}>Maintenance</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="height">Height (cm):</label>
                <input type="number" name="height" id="height" value="{{ profile_data.get('height', '') }}">
            </div>
            
            <div class="form-group">
                <label for="weight">Weight (kg):</label>
                <input type="number" name="weight" id="weight" step="0.1" value="{{ profile_data.get('weight', '') }}">
            </div>
            
            <button type="submit" class="btn btn-primary">💾 Save Changes</button>
            <a href="/admin/user/{{ user.email }}" class="btn btn-secondary">Cancel</a>
        </form>
    </body>
    </html>
    """, user=user, profile_data=profile_data)

@app.route("/admin/find-user")
def admin_find_user():
    if not session.get('admin_authenticated'):
        return "Access denied"

    email = request.args.get('email')
    if not email:
        return "No email provided"

    user = get_user(email)
    if not user:
        return f"User {email} not found"

    # Redirect to the new detailed user view
    return redirect(f"/admin/user/{email}")

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_authenticated', None)
    data_protection.log_data_access('admin', "admin_logout", request.remote_addr)
    return "Logged out successfully. <a href='/admin'>Login again</a>"

@app.route("/admin/export")
def admin_export_data():
    """Export all user data as JSON"""
    admin_key = request.args.get('key')
    if admin_key != 'admin123':
        return "Access denied"

    import json
    from datetime import datetime

    export_data = {
        'exported_at': datetime.now().isoformat(),
        'users': users_data
    }

    response = jsonify(export_data)
    response.headers['Content-Disposition'] = f'attachment; filename=user_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

@app.route("/admin/gdpr-request", methods=["POST"])
def admin_gdpr_request():
    """Handle GDPR data subject requests"""
    if not session.get('admin_authenticated'):
        return "Access denied"

    email = request.form.get('email')
    request_type = request.form.get('request_type')

    result = gdpr_compliance.handle_data_subject_request(email, request_type)
    data_protection.log_data_access(email, f"gdpr_{request_type}", request.remote_addr)

    return jsonify(result)

@app.route("/admin/data-retention")
def admin_data_retention():
    """Check data retention compliance"""
    if not session.get('admin_authenticated'):
        return "Access denied"

    expired_users = gdpr_compliance.check_data_retention_compliance()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head><title>Data Retention Check</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h2>📅 Data Retention Compliance</h2>
        <p>Users with data past retention period: {{ expired_users|length }}</p>
        {% for email in expired_users %}
        <p>• {{ email }}</p>
        {% endfor %}
        <a href="/admin">← Back to Admin</a>
    </body>
    </html>
    """, expired_users=expired_users)

@app.route("/admin/backup")
def admin_backup():
    """Create a backup file"""
    if not session.get('admin_authenticated'):
        return "Access denied"

    import json
    from datetime import datetime

    # Create backup directory if it doesn't exist
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Save backup file
    backup_filename = f"{backup_dir}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_filename, 'w') as f:
        json.dump({
            'exported_at': datetime.now().isoformat(),
            'users': users_data
        }, f, indent=2)

    return f"✅ Backup created: {backup_filename}. <a href='/admin'>Back to admin</a>"

# Food Database search endpoint
@app.route("/food-search")
def food_search():
    """Search the food database"""
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Please provide a search query."}), 400

    results = food_db.search_food(query)
    return jsonify(results)

# API endpoint for food search (used by daily log)
@app.route("/api/food-search")
def api_food_search():
    """API endpoint for searching foods"""
    query = request.args.get('q')
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        # Initialize food database API
        food_api = FoodDatabaseAPI()
        results = food_api.search_all_databases(query, limit_per_db=3)
        
        # Format results for frontend
        formatted_results = []
        for food in results:
            formatted_results.append({
                'name': food.get('name', ''),
                'brand': food.get('brand', ''),
                'source': food.get('source', ''),
                'calories_per_100g': food.get('calories_per_100g', 0),
                'protein_per_100g': food.get('protein_per_100g', 0),
                'carbs_per_100g': food.get('carbs_per_100g', 0),
                'fat_per_100g': food.get('fat_per_100g', 0)
            })
        
        return jsonify(formatted_results)
    except Exception as e:
        print(f"Food search API error: {e}")
        return jsonify([])

# Food Nutrition endpoint
@app.route("/food-nutrition")
def food_nutrition():
    """Return nutrition data for a specific food"""
    food_name = request.args.get('food')
    if not food_name:
        return jsonify({"error": "Please provide a food name."}), 400

    nutrition = food_db.get_nutrition(food_name)
    if nutrition:
        return jsonify(nutrition)
    else:
        return jsonify({"error": f"Nutrition data not found for {food_name}"}), 404

if __name__ == "__main__":
    # Start security monitoring
    security_monitor.start_monitoring()
    app.run(host="0.0.0.0", port=5000, debug=True)