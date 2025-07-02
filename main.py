
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import bcrypt
import openai
from datetime import datetime
import json
from database import get_user, save_user, add_daily_log, get_user_logs, add_weekly_checkin, get_user_checkins
from email_service import email_service
from security_monitoring import SecurityMonitor
import stripe

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# OpenAI setup
openai.api_key = os.getenv('OPENAI_API_KEY', '')

# Stripe setup
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')

# Initialize security monitoring
security_monitor = SecurityMonitor()

@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    user = get_user(session['user_email'])
    if not user:
        session.pop('user_email', None)
        return redirect(url_for('landing_page'))
    
    return render_template('dashboard.html', user=user)

@app.route('/food-search')
def food_search():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    query = request.args.get('q', '')
    results = []

    if query:
        try:
            from food_database import search_food_database
            results = search_food_database(query)
        except Exception as e:
            flash(f'Food search error: {str(e)}')

    return jsonify(results)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        
        user = get_user(email)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_email'] = email
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email', '').lower().strip()
    password = request.form.get('password', '')
    name = request.form.get('name', '').strip()
    
    if get_user(email):
        flash('Account already exists. Please log in.')
        return redirect(url_for('landing_page'))
    
    # Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Save user
    user_data = {
        'email': email,
        'name': name,
        'password': hashed_password,
        'created_at': datetime.now().isoformat()
    }
    save_user(email, user_data)
    
    # Send welcome email
    email_service.send_welcome_email(email, name)
    
    # Add to Mailchimp
    email_service.add_to_mailchimp(email, name, user_data)
    
    session['user_email'] = email
    return redirect(url_for('dashboard'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/send-password-reset', methods=['POST'])
def send_password_reset():
    email = request.form.get('email', '').lower().strip()
    user = get_user(email)
    
    if user:
        # Generate reset token (in production, use proper token generation)
        import secrets
        reset_token = secrets.token_urlsafe(32)
        
        # Store token temporarily (you'd want to add this to database)
        session[f'reset_token_{reset_token}'] = {
            'email': email,
            'expires': (datetime.now().timestamp() + 3600)  # 1 hour
        }
        
        reset_link = url_for('reset_password', token=reset_token, _external=True)
        email_service.send_password_reset_email(email, user['name'], reset_link)
        
        flash('Password reset link sent to your email')
    else:
        flash('If that email exists, we sent a reset link')
    
    return redirect(url_for('forgot_password'))

@app.route('/reset-password/<token>')
def reset_password(token):
    token_data = session.get(f'reset_token_{token}')
    if not token_data or datetime.now().timestamp() > token_data['expires']:
        flash('Reset link expired or invalid')
        return redirect(url_for('forgot_password'))
    
    return render_template('reset_password.html', token=token)

@app.route('/update-password', methods=['POST'])
def update_password():
    token = request.form.get('token')
    password = request.form.get('password')
    confirm_password = request.form.get('confirmPassword')
    
    # Validate token
    token_data = session.get(f'reset_token_{token}')
    if not token_data or datetime.now().timestamp() > token_data['expires']:
        flash('Reset link expired or invalid')
        return redirect(url_for('forgot_password'))
    
    # Validate passwords match
    if password != confirm_password:
        flash('Passwords do not match')
        return render_template('reset_password.html', token=token)
    
    # Hash new password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update user password
    user = get_user(token_data['email'])
    if user:
        user['password'] = hashed_password
        save_user(token_data['email'], user)
        
        # Clear reset token
        session.pop(f'reset_token_{token}', None)
        
        flash('Password updated successfully! Please log in.')
        return redirect(url_for('landing_page'))
    
    flash('User not found')
    return redirect(url_for('forgot_password'))

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    username = request.form.get('username')
    password = request.form.get('password')
    
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    if username == admin_username and password == admin_password:
        session['admin_authenticated'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid admin credentials')
        return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))
    
    from database import get_all_users
    users = get_all_users()
    
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin_login'))

@app.route('/api/food-search')
def api_food_search():
    """API endpoint for food search including restaurants and delivery"""
    if 'user_email' not in session:
        return jsonify([])

    query = request.args.get('q', '')
    results = []

    if query:
        try:
            # Import the food database here to avoid circular imports
            from food_database import FoodDatabaseService
            food_db = FoodDatabaseService()

            # Search all databases including restaurants
            all_results = food_db.search_all_databases(query)

            # Format results for API response
            for food in all_results:
                formatted_food = {
                    'name': food.get('name', ''),
                    'brand': food.get('brand', ''),
                    'source': food.get('source', ''),
                    'calories_per_100g': 0,
                    'serving_size': food.get('serving_size', '100g')
                }

                # Extract calories from nutrients dict if present
                nutrients = food.get('nutrients', {})
                if isinstance(nutrients, dict):
                    calories_str = nutrients.get('calories', '0')
                    if isinstance(calories_str, str):
                        # Extract number from "XXX kcal" format
                        import re
                        calories_match = re.search(r'(\d+)', calories_str)
                        if calories_match:
                            formatted_food['calories_per_100g'] = int(calories_match.group(1))

                results.append(formatted_food)

        except Exception as e:
            print(f'API Food search error: {str(e)}')

    return jsonify(results)

if __name__ == "__main__":
    # Start security monitoring
    security_monitor.start_monitoring()
    
    # Run the Flask app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
