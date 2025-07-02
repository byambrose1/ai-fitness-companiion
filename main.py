from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import bcrypt
import openai
from datetime import datetime
import json
import sqlite3
import re
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

# Track number of signups - in a real app, this would be in a database
import threading
signup_count = 0
signup_lock = threading.Lock()

def validate_email(email):
    """Validate email format and check if it's a real email domain"""
    # Basic email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False

    # Check for common fake email domains
    fake_domains = ['fake.com', 'example.com', 'test.com', 'invalid.com', 'temp.com']
    domain = email.split('@')[1].lower()
    if domain in fake_domains:
        return False

    # Additional validation could include DNS lookup for domain
    return True

def get_current_pricing():
    """
    Determines the current pricing based on the number of signups.
    In a real application, this data would be fetched from a database.
    """
    global signup_count
    is_founding_member = signup_count < 100
    amount = 497 if is_founding_member else 997
    return {
        'is_founding_member': is_founding_member,
        'amount': amount  # Price in pence
    }

@app.route('/')
def landing_page():
    # If user is logged in and comes to landing page with email param, redirect to questionnaire
    email = request.args.get('email')
    if email and 'user_email' in session and session['user_email'] == email:
        return redirect(url_for('questionnaire'))

    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    print(f'DASHBOARD: Session check - user_email in session: {"user_email" in session}')
    if 'user_email' not in session:
        print('DASHBOARD: No user in session, redirecting to landing page')
        return redirect(url_for('landing_page'))

    print(f'DASHBOARD: Loading user data for {session["user_email"]}')
    user = get_user(session['user_email'])
    if not user:
        print('DASHBOARD: User not found in database, clearing session')
        session.pop('user_email', None)
        return redirect(url_for('landing_page'))

    print(f'DASHBOARD: User loaded successfully, profile_data keys: {list(user.get("profile_data", {}).keys())}')

    # Calculate dashboard data
    from datetime import datetime, timedelta

    # Calculate days since signup
    created_at = datetime.fromisoformat(user['created_at'])
    days_since_signup = (datetime.now() - created_at).days

    # Get user logs for stats
    daily_logs = user.get('daily_logs', [])
    total_logs = len(daily_logs)

    # Calculate streak (simplified - consecutive days with logs)
    streak_days = min(total_logs, 7)  # Cap at 7 for new users

    # Get recent score from latest log
    recent_score = None
    if daily_logs:
        recent_score = daily_logs[-1].get('overallScore', 8)

    # Contextual message based on user data
    profile_data = user.get('profile_data', {})
    goal = profile_data.get('goal', 'general_fitness')

    contextual_messages = {
        'weight_loss': 'Focus on creating a sustainable calorie deficit today 💪',
        'muscle_gain': 'Fuel your muscles with protein and progressive overload 🏋️',
        'general_fitness': 'Every small step counts towards your wellness journey 🌟',
        'endurance': 'Build your stamina one workout at a time 🏃',
        'strength': 'Strength comes from consistency, not perfection 💪'
    }
    contextual_message = contextual_messages.get(goal, 'You\'re doing great - keep up the momentum! 🌟')

    # Motivation content based on progress
    if total_logs == 0:
        motivation_content = '''
        <div class="motivation-section first-time">
            <h3>🌟 Welcome to Your Journey!</h3>
            <p>Ready to start tracking your progress? Your first daily log is just a click away!</p>
        </div>
        '''
    elif total_logs < 7:
        motivation_content = '''
        <div class="motivation-section building-habit">
            <h3>🔥 Building Your Habit!</h3>
            <p>You're off to a great start! Consistency is key - keep logging daily to build momentum.</p>
        </div>
        '''
    else:
        motivation_content = '''
        <div class="motivation-section established">
            <h3>💪 You're Crushing It!</h3>
            <p>Your consistency is impressive! Keep up this amazing progress.</p>
        </div>
        '''

    return render_template('dashboard.html', 
                         user=user,
                         days_since_signup=days_since_signup,
                         total_logs=total_logs,
                         streak_days=streak_days,
                         recent_score=recent_score,
                         contextual_message=contextual_message,
                         motivation_content=motivation_content)

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
        except ImportError:
            results = []
            flash('Food database not available')
        except Exception as e:
            results = []
            flash(f'Food search error: {str(e)}')

    return jsonify(results)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')

        print(f'LOGIN ATTEMPT: email={email}, password_length={len(password) if password else 0}')

        if not email or not password:
            print('LOGIN FAILED: Missing email or password')
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                return jsonify({'success': False, 'message': 'Email and password are required'})
            flash('Email and password are required')
            return render_template('index.html')

        user = get_user(email)
        print(f'USER LOOKUP: user_found={user is not None}')

        if user:
            password_match = bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))
            print(f'PASSWORD CHECK: matches={password_match}')

            if password_match:
                session['user_email'] = email
                print(f'LOGIN SUCCESS: Setting session for {email}')
                # Check for AJAX request
                is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                          request.headers.get('Content-Type') == 'application/json' or 
                          request.is_json)
                if is_ajax:
                    return jsonify({'success': True, 'redirect': url_for('dashboard')})
                return redirect(url_for('dashboard'))

        print('LOGIN FAILED: Invalid credentials')
        # Check for AJAX request
        is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                  request.headers.get('Content-Type') == 'application/json' or 
                  request.is_json)
        if is_ajax:
            return jsonify({'success': False, 'message': 'Invalid email or password'})
        flash('Invalid email or password')

    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    global signup_count

    email = request.form.get('email', '').lower().strip()
    password = request.form.get('password', '')
    name = request.form.get('name', '').strip()

    print(f'Registration attempt: email={email}, name={name}, password_length={len(password) if password else 0}')

    # Check if this is an AJAX request
    is_ajax = request.headers.get('Content-Type') == 'application/json' or request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Validate required fields
    if not email or not password or not name:
        print('Validation failed: Missing required fields')
        error_msg = 'All fields are required.'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg)
        return redirect(url_for('landing_page'))

    # Validate email format
    if not validate_email(email):
        print(f'Validation failed: Invalid email format for {email}')
        error_msg = 'Please enter a valid email address.'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg)
        return redirect(url_for('landing_page'))

    # Check if user already exists
    try:
        existing_user = get_user(email)
        if existing_user:
            print(f'Registration failed: User {email} already exists')
            error_msg = 'Account already exists with this email. Please try logging in instead.'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg, 'existing_user': True})
            flash(error_msg)
            return redirect(url_for('landing_page'))
    except Exception as e:
        print(f'Error checking existing user: {e}')
        error_msg = 'Database error. Please try again.'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg)
        return redirect(url_for('landing_page'))

    # Hash password
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print('Password hashed successfully')
    except Exception as e:
        print(f'Password hashing failed: {e}')
        error_msg = 'Password processing error. Please try again.'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg)
        return redirect(url_for('landing_page'))

    # Save user
    try:
        user_data = {
            'email': email,
            'name': name,
            'password': hashed_password,
            'created_at': datetime.now().isoformat(),
            'subscription_tier': 'free',
            'subscription_status': 'active',
            'profile_data': {}
        }
        print(f'Attempting to save user: {email}')
        save_user(user_data)
        print(f'User saved successfully: {email}')
    except Exception as e:
        print(f'Database save failed: {e}')
        error_msg = 'Failed to create account. Database error.'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg)
        return redirect(url_for('landing_page'))

    # Increment signup count (thread-safe)
    try:
        with signup_lock:
            signup_count += 1
            print(f'Signup count incremented to: {signup_count}')
    except Exception as e:
        print(f'Signup count increment failed: {e}')

    # Try to send welcome email (don't fail registration if email fails)
    try:
        email_service.send_welcome_email(email, name)
        print('Welcome email sent successfully')
    except Exception as e:
        print(f'Welcome email failed: {e}')

    # Try to add to Mailchimp (don't fail registration if this fails)
    try:
        email_service.add_to_mailchimp(email, name, user_data)
        print('Mailchimp add successful')
    except Exception as e:
        print(f'Mailchimp add failed: {e}')

    # Set session and return appropriate response
    try:
        session['user_email'] = email
        print(f'Session set for user: {email}')

        if is_ajax:
            return jsonify({
                'success': True, 
                'message': 'Account created successfully!',
                'redirect': url_for('dashboard')
            })
        else:
            flash('Account created successfully! Welcome to your fitness journey!')
            return redirect(url_for('dashboard'))
    except Exception as e:
        print(f'Session/redirect failed: {e}')
        error_msg = 'Account created but login failed. Please try logging in.'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg)
        return redirect(url_for('landing_page'))

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
        save_user(user)

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

@app.route('/admin')
def admin():
    """Admin login page redirect"""
    return redirect(url_for('admin_login'))

@app.route('/admin/user/<email>/change-subscription', methods=['POST'])
def admin_change_subscription():
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401

    email = request.form.get('email')
    new_tier = request.form.get('tier')

    user = get_user(email)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Update subscription
    user['subscription_tier'] = new_tier
    user['subscription_status'] = 'active'
    save_user(user)

    return jsonify({'success': True, 'message': f'Subscription changed to {new_tier}'})

@app.route('/admin/user/<email>/cancel', methods=['POST'])
def admin_cancel_user():
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401

    email = request.form.get('email')

    user = get_user(email)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Cancel subscription but don't delete user
    user['subscription_status'] = 'cancelled'
    user['subscription_tier'] = 'free'
    save_user(user)

    return jsonify({'success': True, 'message': 'User subscription cancelled'})

@app.route('/admin/user/<email>/delete', methods=['POST'])
def admin_delete_user():
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401

    email = request.form.get('email')

    # Delete user from database
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()

    # Delete user logs first
    cursor.execute('DELETE FROM daily_logs WHERE user_email = ?', (email,))
    cursor.execute('DELETE FROM weekly_checkins WHERE user_email = ?', (email,))
    cursor.execute('DELETE FROM users WHERE email = ?', (email,))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'User deleted successfully'})

@app.route('/admin/stripe-dashboard')
def admin_stripe_dashboard():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))

    # Get Stripe customers and revenue data
    try:
        customers = stripe.Customer.list(limit=100)
        subscriptions = stripe.Subscription.list(limit=100)

        # Calculate revenue
        total_revenue = 0
        active_subscriptions = 0

        for sub in subscriptions.data:
            if sub.status == 'active':
                active_subscriptions += 1
                total_revenue += sub.items.data[0].price.unit_amount / 100  # Convert from pence to pounds

        stripe_data = {
            'customers': customers.data,
            'subscriptions': subscriptions.data,
            'total_revenue': total_revenue,
            'active_subscriptions': active_subscriptions
        }

    except Exception as e:
        stripe_data = {
            'error': str(e),
            'customers': [],
            'subscriptions': [],
            'total_revenue': 0,
            'active_subscriptions': 0
        }

    return render_template('admin_stripe.html', stripe_data=stripe_data)

@app.route('/admin/stats')
def admin_stats():
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401

    from database import get_all_users
    users = get_all_users()

    # Calculate stats
    total_users = len(users)
    premium_users = len([u for u in users if u.get('subscription_tier') == 'premium'])
    free_users = len([u for u in users if u.get('subscription_tier') == 'free'])
    cancelled_users = len([u for u in users if u.get('subscription_status') == 'cancelled'])

    # Calculate total logs
    total_logs = sum(len(u.get('daily_logs', [])) for u in users)
    total_checkins = sum(len(u.get('weekly_checkins', [])) for u in users)

    stats = {
        'total_users': total_users,
        'premium_users': premium_users,
        'free_users': free_users,
        'cancelled_users': cancelled_users,
        'total_logs': total_logs,
        'total_checkins': total_checkins
    }

    return jsonify(stats)

@app.route('/subscription')
def subscription():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    # Get pricing information
    pricing = get_current_pricing()
    users_until_price_change = max(0, 100 - signup_count)

    return render_template('subscription.html', 
                         current_tier=user.get('subscription_tier', 'free'),
                         email=user['email'],
                         pricing=pricing,
                         users_until_price_change=users_until_price_change,
                         stripe_publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY', ''))

@app.route('/premium')
def premium():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    # Redirect to subscription page
    return redirect(url_for('subscription'))

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    if 'user_email' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        user = get_user(session['user_email'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get current pricing
        pricing = get_current_pricing()

        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': 'AI Fitness Companion - Premium',
                        'description': 'Unlimited AI insights, meal plans, and advanced analytics' + 
                                     (' - FOUNDING MEMBER PRICING' if pricing['is_founding_member'] else '')
                    },
                    'unit_amount': pricing['amount'],
                    'recurring': {
                        'interval': 'month'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            customer_email=user['email'],
            success_url=url_for('subscription_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('subscription', _external=True),
            metadata={
                'user_email': user['email']
            }
        )

        return jsonify({'id': checkout_session.id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/subscription-success')
def subscription_success():
    session_id = request.args.get('session_id')

    if not session_id:
        flash('Invalid session')
        return redirect(url_for('subscription'))

    try:
        # Retrieve the session
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        # Update user subscription
        user_email = checkout_session.metadata.get('user_email')
        if user_email:
            user = get_user(user_email)
            if user:
                user['subscription_tier'] = 'premium'
                user['subscription_status'] = 'active'
                user['stripe_customer_id'] = checkout_session.customer
                save_user(user)

                flash('Welcome to Premium! Your subscription is now active.')
            else:
                flash('User not found')
        else:
            flash('Invalid session data')

    except Exception as e:
        flash(f'Error processing subscription: {str(e)}')

    return redirect(url_for('dashboard'))

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    if 'user_email' not in session:
        print('QUESTIONNAIRE: No user in session, redirecting to landing page')
        return redirect(url_for('landing_page'))

    if request.method == 'POST':
        print(f'QUESTIONNAIRE POST: User {session["user_email"]} submitting questionnaire')
        user = get_user(session['user_email'])
        if user:
            # Save questionnaire data to user profile
            profile_data = {
                'goal': request.form.get('goal'),
                'activity_level': request.form.get('activity_level'),
                'dietary_preferences': request.form.get('dietary_preferences'),
                'health_conditions': request.form.get('health_conditions'),
                'questionnaire_completed': True
            }
            print(f'QUESTIONNAIRE: Saving profile data: {profile_data}')
            user['profile_data'].update(profile_data)
            save_user(user)
            print('QUESTIONNAIRE: Profile saved successfully, redirecting to dashboard')

            flash('Profile updated successfully!')
            return redirect(url_for('dashboard'))
        else:
            print('QUESTIONNAIRE ERROR: User not found in database')
            flash('User not found. Please log in again.')
            return redirect(url_for('landing_page'))


@app.route('/daily-log')
def daily_log():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    return render_template('daily-log.html', user=user, datetime=datetime)

@app.route('/save-daily-log', methods=['POST'])
def save_daily_log():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    # Collect form data
    log_data = {
        'date': datetime.now().isoformat(),
        'mood': request.form.get('mood'),
        'energy_level': request.form.get('energy_level'),
        'stress_level': request.form.get('stress_level'),
        'sleep_hours': request.form.get('sleep_hours'),
        'sleep_quality': request.form.get('sleep_quality'),
        'workout': request.form.get('workout'),
        'workout_intensity': request.form.get('workout_intensity'),
        'workout_duration': request.form.get('workout_duration'),
        'food_log': request.form.get('food_log'),
        'water_intake': request.form.get('water_intake'),
        'weight': request.form.get('weight'),
        'notes': request.form.get('notes'),
        'tracking_devices': request.form.get('tracking_devices')
    }

    # Collect device-specific data
    device_data = {}

    # Apple Health data
    apple_data = {
        'steps': request.form.get('apple_steps'),
        'active_calories': request.form.get('apple_active_calories'),
        'exercise_time': request.form.get('apple_exercise_time'),
        'stand_hours': request.form.get('apple_stand_hours'),
        'heart_rate': request.form.get('apple_heart_rate'),
        'sleep': request.form.get('apple_sleep')
    }
    if any(apple_data.values()):
        device_data['apple_health'] = apple_data

    # Fitbit data
    fitbit_data = {
        'steps': request.form.get('fitbit_steps'),
        'zone_minutes': request.form.get('fitbit_zone_minutes'),
        'sleep_score': request.form.get('fitbit_sleep_score'),
        'resting_hr': request.form.get('fitbit_resting_hr'),
        'floors': request.form.get('fitbit_floors'),
        'calories': request.form.get('fitbit_calories')
    }
    if any(fitbit_data.values()):
        device_data['fitbit'] = fitbit_data

    # Garmin data
    garmin_data = {
        'steps': request.form.get('garmin_steps'),
        'body_battery': request.form.get('garmin_body_battery'),
        'stress': request.form.get('garmin_stress'),
        'vo2_max': request.form.get('garmin_vo2_max'),
        'intensity_minutes': request.form.get('garmin_intensity_minutes'),
        'sleep_score': request.form.get('garmin_sleep_score')
    }
    if any(garmin_data.values()):
        device_data['garmin'] = garmin_data

    # Oura data
    oura_data = {
        'readiness': request.form.get('oura_readiness'),
        'sleep_score': request.form.get('oura_sleep_score'),
        'activity': request.form.get('oura_activity'),
        'hrv': request.form.get('oura_hrv'),
        'resting_hr': request.form.get('oura_resting_hr'),
        'temperature': request.form.get('oura_temperature')
    }
    if any(oura_data.values()):
        device_data['oura'] = oura_data

    # Samsung data
    samsung_data = {
        'steps': request.form.get('samsung_steps'),
        'active_time': request.form.get('samsung_active_time'),
        'sleep': request.form.get('samsung_sleep'),
        'heart_rate': request.form.get('samsung_heart_rate'),
        'stress': request.form.get('samsung_stress'),
        'calories': request.form.get('samsung_calories')
    }
    if any(samsung_data.values()):
        device_data['samsung'] = samsung_data

    # Polar data
    polar_data = {
        'steps': request.form.get('polar_steps'),
        'training_load': request.form.get('polar_training_load'),
        'recovery': request.form.get('polar_recovery'),
        'sleep_score': request.form.get('polar_sleep_score'),
        'rhr': request.form.get('polar_rhr'),
        'active_calories': request.form.get('polar_active_calories')
    }
    if any(polar_data.values()):
        device_data['polar'] = polar_data

    # Suunto data
    suunto_data = {
        'steps': request.form.get('suunto_steps'),
        'recovery_time': request.form.get('suunto_recovery_time'),
        'training_stress': request.form.get('suunto_training_stress'),
        'sleep': request.form.get('suunto_sleep'),
        'resources': request.form.get('suunto_resources'),
        'calories': request.form.get('suunto_calories')
    }
    if any(suunto_data.values()):
        device_data['suunto'] = suunto_data

    # Add device data to log
    if device_data:
        log_data['device_data'] = device_data

    # Calculate overall score (simplified)
    score = 5  # Base score
    if log_data['mood'] and log_data['mood'] in ['excellent', 'good']:
        score += 1
    if log_data['water_intake'] and log_data['water_intake'] in ['good', 'excellent']:
        score += 1
    if log_data['sleep_hours'] and 7 <= float(log_data['sleep_hours']) <= 9:
        score += 1.5
    if log_data['workout'] and log_data['workout'] != 'rest':
        score += 1.5

    log_data['overallScore'] = min(10, score)

    # Save to database
    add_daily_log(session['user_email'], log_data)

    flash('Daily log saved successfully!')
    return redirect(url_for('dashboard'))

@app.route('/submit-daily-log', methods=['POST'])
def submit_daily_log():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    # Collect form data
    log_data = {
        'date': request.form.get('date', datetime.now().isoformat()),
        'mood': request.form.get('mood'),
        'energy_level': request.form.get('energy_level'),
        'stress_level': request.form.get('stress_level'),
        'sleep_hours': request.form.get('sleep_hours'),
        'workout': request.form.get('workout'),
        'workout_duration': request.form.get('workout_duration'),
        'food_log': request.form.get('food_log'),
        'water_intake': request.form.get('water_intake'),
        'weight': request.form.get('weight'),
        'tracking_devices': request.form.get('tracking_devices'),
        'notes': request.form.get('notes'),
        'timestamp': datetime.now().isoformat()
    }

    # Calculate overall score (simplified)
    score = 5  # Base score

    # Mood scoring
    if log_data['mood']:
        mood_scores = {'excellent': 2, 'good': 1.5, 'okay': 1, 'low': 0.5}
        score += mood_scores.get(log_data['mood'], 0)

    # Water scoring
    if log_data['water_intake']:
        water_scores = {'excellent': 1.5, 'good': 1, 'moderate': 0.5, 'low': 0}
        score += water_scores.get(log_data['water_intake'], 0)

    # Workout scoring
    if log_data['workout'] and log_data['workout'] != 'rest':
        score += 1.5
    elif log_data['workout'] == 'rest':
        score += 0.5

    # Sleep scoring
    if log_data['sleep_hours']:
        try:
            sleep_hours = float(log_data['sleep_hours'])
            if 7 <= sleep_hours <= 9:
                score += 1.5
            elif 6 <= sleep_hours < 7 or 9 < sleep_hours <= 10:
                score += 1
        except ValueError:
            pass

    # Stress level scoring (inverted - lower stress = higher score)
    if log_data['stress_level']:
        try:
            stress = int(log_data['stress_level'])
            if stress <= 3:
                score += 0.5
            elif stress >= 8:
                score -= 0.5
        except ValueError:
            pass

    log_data['overallScore'] = min(10, score)

    # Save to database
    add_daily_log(session['user_email'], log_data)

    flash('Daily log saved successfully!')
    return redirect(url_for('dashboard'))

@app.route('/weekly-checkin')
def weekly_checkin():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    return render_template('weekly_checkin.html', user=user, email=user['email'], today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/submit-weekly-checkin', methods=['POST'])
def submit_weekly_checkin():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    # Collect form data
    checkin_data = {
        'date': datetime.now().isoformat(),
        'weight_change': request.form.get('weight_change'),
        'energy_level': request.form.get('energy_level'),
        'motivation_level': request.form.get('motivation_level'),
        'biggest_challenge': request.form.get('biggest_challenge'),
        'biggest_win': request.form.get('biggest_win'),
        'goals_next_week': request.form.get('goals_next_week'),
        'sleep_pattern': request.form.get('sleep_pattern'),
        'stress_level': request.form.get('stress_level'),
        'notes': request.form.get('notes')
    }

    # Save to database
    add_weekly_checkin(session['user_email'], checkin_data)

    flash('Weekly check-in saved successfully!')
    return redirect(url_for('dashboard'))


@app.route('/ai-chat')
def ai_chat():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    return render_template('ai_chat.html', user=user)

@app.route('/ai-response', methods=['POST'])
def ai_response():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    question = request.form.get('question', '')
    if not question:
        flash('Please enter a question')
        return redirect(url_for('ai_chat'))

    # Simple AI response for now
    ai_response = f"Thanks for asking: '{question}'. Based on your profile, here's my advice: Stay consistent with your logging and focus on gradual improvements. (Full AI integration coming soon!)"
    
    flash(f"AI Response: {ai_response}")
    return redirect(url_for('ai_chat'))

@app.route('/ai-chat-message', methods=['POST'])
def ai_chat_message():
    if 'user_email' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user = get_user(session['user_email'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    message = request.json.get('message', '')
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Check subscription tier for AI limits
    if user.get('subscription_tier') == 'free':
        # Implement usage limits for free tier
        pass

    try:
        # Simple AI response (you can enhance this with OpenAI)
        response = f"Thanks for your message: '{message}'. I'm here to help with your fitness journey! (AI integration coming soon)"

        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500




@app.route('/connect-devices')
def connect_devices():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    return render_template('connect_devices.html', user=user)

@app.route('/select-device', methods=['POST'])
def select_device():
    if 'user_email' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user = get_user(session['user_email'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    device = request.json.get('device')
    if not device:
        return jsonify({'error': 'No device specified'}), 400

    # Update user's preferred tracking device
    if 'profile_data' not in user:
        user['profile_data'] = {}

    user['profile_data']['preferred_device'] = device
    save_user(user)

    # Return device-specific manual entry instructions
    device_instructions = {
        'oura': {
            'name': 'Oura Ring',
            'status': 'Connection coming soon',
            'manual_fields': ['Sleep Score (0-100)', 'Readiness Score (0-100)', 'HRV (ms)', 'Resting Heart Rate (bpm)', 'Body Temperature (°C)'],
            'description': 'Enter your data manually in the same format as your Oura app.'
        },
        'fitbit': {
            'name': 'Fitbit',
            'status': 'Connected (manual entry)',
            'manual_fields': ['Steps', 'Active Minutes', 'Heart Rate (bpm)', 'Sleep Hours', 'Calories Burned'],
            'description': 'Enter your Fitbit data manually until auto-sync is available.'
        },
        'garmin': {
            'name': 'Garmin',
            'status': 'Connection coming soon',
            'manual_fields': ['Steps', 'Active Minutes', 'Stress Score', 'Body Battery', 'VO2 Max'],
            'description': 'Device connection coming soon. Please enter your data manually.'
        },
        'apple_health': {
            'name': 'Apple Health',
            'status': 'Connection coming soon (requires native app)',
            'manual_fields': ['Steps', 'Heart Rate (bpm)', 'Sleep Hours', 'Active Energy (kcal)', 'Mindful Minutes'],
            'description': 'Apple Health connection requires a native app. Enter data manually for now.'
        },
        'google_fit': {
            'name': 'Google Fit',
            'status': 'Connection coming soon (requires native app)',
            'manual_fields': ['Steps', 'Active Minutes', 'Heart Rate (bpm)', 'Distance (km)', 'Calories'],
            'description': 'Google Fit connection requires a native app. Enter data manually for now.'
        }
    }

    return jsonify({
        'success': True,
        'device_info': device_instructions.get(device, {
            'name': device,
            'status': 'Unknown device',
            'manual_fields': [],
            'description': 'Please select a supported device.'
        })
    })


    return redirect(url_for('dashboard'))



    # Save to database
    add_daily_log(session['user_email'], log_data)

    flash('Daily log saved successfully!')
    return redirect(url_for('dashboard'))



    print('QUESTIONNAIRE GET: Rendering questionnaire page')
    return render_template('questionnaire.html')

@app.route('/downgrade', methods=['POST'])
def downgrade():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    # Update subscription to free
    user['subscription_tier'] = 'free'
    user['subscription_status'] = 'active'
    save_user(user)

    flash('Subscription downgraded to Free plan')
    return redirect(url_for('subscription'))

@app.route('/cancel-subscription', methods=['POST'])
def cancel_subscription():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))

    # Cancel subscription
    user['subscription_tier'] = 'free'
    user['subscription_status'] = 'cancelled'
    save_user(user)

    flash('Your subscription has been cancelled. You can still use the free features.')
    return redirect(url_for('dashboard'))

@app.route('/delete-account', methods=['POST'])
def delete_account():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))

    email = session['user_email']

    # Delete user data
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM daily_logs WHERE user_email = ?', (email,))
    cursor.execute('DELETE FROM weekly_checkins WHERE user_email = ?', (email,))
    cursor.execute('DELETE FROM users WHERE email = ?', (email,))

    conn.commit()
    conn.close()

    # Clear session
    session.clear()

    flash('Your account has been permanently deleted.')
    return redirect(url_for('landing_page'))

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
                else:
                    # Handle direct calorie values
                    formatted_food['calories_per_100g'] = food.get('calories_per_100g', 0)

                results.append(formatted_food)

        except Exception as e:
            print(f'API Food search error: {str(e)}')

    return jsonify(results)

if __name__ == "__main__":
    # Start security monitoring
    try:
        security_monitor.start_monitoring()
    except Exception as e:
        print(f"Security monitoring failed to start: {e}")

    # Run the Flask app with port fallback
    port = int(os.getenv('PORT', 5000))
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Port {port} is in use, trying port {port + 1}")
            app.run(host='0.0.0.0', port=port + 1, debug=True)
        else:
            raise