
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash
import json
import os
import bcrypt
from datetime import datetime, timedelta
import openai
import stripe
from email_service import send_welcome_email, add_to_mailchimp
from database import get_user, save_user, users_data
from food_database import search_food_database, get_nutrition_info
from fitness_tracker_apis import FitnessTrackerAPI
from oauth_handlers import setup_oauth_routes
from notifications import NotificationManager
from security_monitoring import SecurityMonitor
from data_protection import DataProtectionManager
from gdpr_compliance import GDPRComplianceManager

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Initialize services
openai.api_key = os.getenv('OPENAI_API_KEY', '')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')

fitness_api = FitnessTrackerAPI()
notification_manager = NotificationManager()
security_monitor = SecurityMonitor()
data_protection = DataProtectionManager()
gdpr_compliance = GDPRComplianceManager()

# Setup OAuth routes
setup_oauth_routes(app, fitness_api)

@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        goal = request.form.get('goal')
        age = request.form.get('age')
        gender = request.form.get('gender')
        height = request.form.get('height')
        weight = request.form.get('weight')
        activity_level = request.form.get('activityLevel')
        sleep_hours = request.form.get('sleepHours')
        stress_level = request.form.get('stressLevel')
        motivation = request.form.get('motivation')
        
        # Validate required fields
        if not all([name, email, password]):
            flash('Please fill in all required fields.')
            return redirect(url_for('questionnaire'))
        
        # Check if user already exists
        existing_user = get_user(email)
        if existing_user:
            flash('An account with this email already exists. Please sign in.')
            return redirect(url_for('signin'))
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user data
        user_data = {
            'name': name,
            'email': email,
            'password': hashed_password.decode('utf-8'),
            'created_at': datetime.now().isoformat(),
            'subscription_tier': 'free',
            'subscription_status': 'active',
            'stripe_customer_id': None,
            'subscription_end_date': None,
            'profile_data': {
                'goal': goal,
                'age': age,
                'gender': gender,
                'height': height,
                'weight': weight,
                'activityLevel': activity_level,
                'sleepHours': sleep_hours,
                'stressLevel': stress_level,
                'motivation': motivation
            },
            'daily_logs': [],
            'weekly_checkins': [],
            'ai_questions_count': 0,
            'ai_questions_reset_date': datetime.now().isoformat()
        }
        
        # Save user
        save_user(user_data)
        
        # Send welcome email
        try:
            send_welcome_email(email, name)
            add_to_mailchimp(email, name)
        except Exception as e:
            print(f"Email service error: {e}")
        
        # Set session
        session['user_email'] = email
        session['user_name'] = name
        
        return redirect(url_for('dashboard'))
    
    return render_template('results.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = get_user(email)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_email'] = email
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.')
    
    return render_template('index.html')

@app.route('/signout')
def signout():
    session.clear()
    return redirect(url_for('landing_page'))

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))
    
    # Get recent logs
    recent_logs = user.get('daily_logs', [])[-7:]  # Last 7 days
    
    return render_template('dashboard.html', user=user, recent_logs=recent_logs)

@app.route('/daily-log', methods=['GET', 'POST'])
def daily_log():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    if request.method == 'POST':
        user = get_user(session['user_email'])
        
        # Get form data
        log_data = {
            'date': datetime.now().isoformat(),
            'weight': request.form.get('weight'),
            'energy': request.form.get('energy'),
            'mood': request.form.get('mood'),
            'sleep': request.form.get('sleep'),
            'exercise': request.form.get('exercise'),
            'water': request.form.get('water'),
            'food': request.form.get('food'),
            'notes': request.form.get('notes'),
            'cycle_day': request.form.get('cycle_day'),
            'cycle_phase': request.form.get('cycle_phase'),
            'symptoms': request.form.getlist('symptoms')
        }
        
        # Add to user's daily logs
        if 'daily_logs' not in user:
            user['daily_logs'] = []
        user['daily_logs'].append(log_data)
        
        # Save user data
        save_user(user)
        
        flash('Daily log saved successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('daily-log.html')

@app.route('/weekly-checkin', methods=['GET', 'POST'])
def weekly_checkin():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    if request.method == 'POST':
        user = get_user(session['user_email'])
        
        checkin_data = {
            'date': datetime.now().isoformat(),
            'overall_feeling': request.form.get('overall_feeling'),
            'energy_trend': request.form.get('energy_trend'),
            'sleep_quality': request.form.get('sleep_quality'),
            'stress_levels': request.form.get('stress_levels'),
            'exercise_consistency': request.form.get('exercise_consistency'),
            'nutrition_satisfaction': request.form.get('nutrition_satisfaction'),
            'cycle_regularity': request.form.get('cycle_regularity'),
            'goal_progress': request.form.get('goal_progress'),
            'challenges': request.form.get('challenges'),
            'wins': request.form.get('wins'),
            'focus_next_week': request.form.get('focus_next_week')
        }
        
        if 'weekly_checkins' not in user:
            user['weekly_checkins'] = []
        user['weekly_checkins'].append(checkin_data)
        
        save_user(user)
        
        flash('Weekly check-in completed!')
        return redirect(url_for('dashboard'))
    
    return render_template('weekly_checkin.html')

@app.route('/ai-chat', methods=['GET', 'POST'])
def ai_chat():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    user = get_user(session['user_email'])
    
    # Check AI usage limits
    if user['subscription_tier'] == 'free':
        # Reset counter if a week has passed
        reset_date = datetime.fromisoformat(user.get('ai_questions_reset_date', datetime.now().isoformat()))
        if datetime.now() - reset_date > timedelta(days=7):
            user['ai_questions_count'] = 0
            user['ai_questions_reset_date'] = datetime.now().isoformat()
            save_user(user)
        
        if user.get('ai_questions_count', 0) >= 3:
            flash('You\'ve reached your weekly AI question limit. Upgrade to Premium for unlimited access!')
            return redirect(url_for('subscription'))
    
    if request.method == 'POST':
        question = request.form.get('question')
        
        if not question:
            flash('Please enter a question.')
            return render_template('ai_chat.html', user=user)
        
        try:
            # Prepare context for AI
            context = f"""
            User Profile:
            - Goal: {user['profile_data'].get('goal', 'Not specified')}
            - Age: {user['profile_data'].get('age', 'Not specified')}
            - Activity Level: {user['profile_data'].get('activityLevel', 'Not specified')}
            
            Recent Daily Logs:
            {json.dumps(user.get('daily_logs', [])[-5:], indent=2)}
            
            Recent Check-ins:
            {json.dumps(user.get('weekly_checkins', [])[-2:], indent=2)}
            
            Connected Devices Data:
            {json.dumps(user.get('device_data', {}), indent=2)}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"""You are a supportive, knowledgeable fitness and wellness coach specializing in hormone-aware health guidance. 
                    
                    Context about this user: {context}
                    
                    Provide personalized, practical advice based on their data. Be encouraging, specific, and consider hormonal fluctuations, especially for menstrual cycle awareness. Keep responses concise but helpful."""},
                    {"role": "user", "content": question}
                ],
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            # Update usage count for free users
            if user['subscription_tier'] == 'free':
                user['ai_questions_count'] = user.get('ai_questions_count', 0) + 1
                save_user(user)
            
            return render_template('ai_chat.html', user=user, question=question, response=ai_response)
            
        except Exception as e:
            flash(f'Sorry, there was an error processing your question: {str(e)}')
    
    return render_template('ai_chat.html', user=user)

@app.route('/food-search')
def food_search():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    query = request.args.get('q', '')
    results = []
    
    if query:
        try:
            results = search_food_database(query)
        except Exception as e:
            flash(f'Food search error: {str(e)}')
    
    return jsonify(results)

@app.route('/connect-devices')
def connect_devices():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    user = get_user(session['user_email'])
    return render_template('connect_devices.html', user=user)

@app.route('/subscription')
def subscription():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    user = get_user(session['user_email'])
    return render_template('subscription.html', user=user, stripe_pk=os.getenv('STRIPE_PUBLISHABLE_KEY'))

@app.route('/create-subscription', methods=['POST'])
def create_subscription():
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    try:
        user = get_user(session['user_email'])
        
        # Create Stripe customer if doesn't exist
        if not user.get('stripe_customer_id'):
            customer = stripe.Customer.create(
                email=user['email'],
                name=user['name']
            )
            user['stripe_customer_id'] = customer.id
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=user['stripe_customer_id'],
            items=[{'price': 'price_premium_monthly'}],  # Replace with your actual price ID
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent']
        )
        
        user['subscription_tier'] = 'premium'
        user['subscription_status'] = 'active'
        save_user(user)
        
        return jsonify({
            'subscriptionId': subscription.id,
            'clientSecret': subscription.latest_invoice.payment_intent.client_secret
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/features-comparison')
def features_comparison():
    return render_template('features-comparison.html')

@app.route('/wearables-guide')
def wearables_guide():
    return render_template('wearables-guide.html')

if __name__ == "__main__":
    # Create a test user for easy login
    try:
        test_email = "test@example.com"
        if not get_user(test_email):
            test_user = {
                'name': 'Test User',
                'email': test_email,
                'password': bcrypt.hashpw('testpass123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                'created_at': datetime.now().isoformat(),
                'subscription_tier': 'premium',  # Give test user premium access
                'subscription_status': 'active',
                'stripe_customer_id': None,
                'subscription_end_date': None,
                'profile_data': {
                    'goal': 'fat_loss',
                    'age': 30,
                    'gender': 'other',
                    'height': '170',
                    'weight': '70',
                    'activityLevel': 'moderate',
                    'sleepHours': '7-8',
                    'stressLevel': '5',
                    'motivation': 'I want to get healthier and feel more confident!'
                },
                'daily_logs': [],
                'weekly_checkins': []
            }
            save_user(test_user)
            users_data[test_email] = test_user
            print(f"✅ Test user created: {test_email} / testpass123")
    except Exception as e:
        print(f"⚠️ Could not create test user: {e}")

    # Start security monitoring
    security_monitor.start_monitoring()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
