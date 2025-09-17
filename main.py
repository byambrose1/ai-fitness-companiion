"""
AI Fitness Companion - Enhanced Flask Application
A comprehensive fitness tracking app with personalized AI coaching
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import bcrypt
import json
import os
from datetime import datetime, timedelta
import openai
from dotenv import load_dotenv
import secrets
import re
from personalisation import generate_personalized_dashboard_content

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))

# OpenAI configuration
openai.api_key = os.getenv('OPENAI_API_KEY')

# Database configuration
DATABASE = 'fitness_app.db'

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            date_of_birth TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            profile_data TEXT,
            questionnaire_completed BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Daily logs table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            weight REAL,
            sleep_hours REAL,
            water_intake TEXT,
            stress_level INTEGER,
            mood TEXT,
            food_log TEXT,
            workout TEXT,
            workout_duration INTEGER,
            notes TEXT,
            score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, date)
        )
    ''')
    
    # Health data table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS health_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            steps INTEGER,
            heart_rate REAL,
            calories_burned INTEGER,
            active_minutes INTEGER,
            source TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user(email):
    """Get user by email"""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if user:
        user_dict = dict(user)
        if user_dict.get('profile_data'):
            try:
                user_dict['profile_data'] = json.loads(user_dict['profile_data'])
            except json.JSONDecodeError:
                user_dict['profile_data'] = {}
        else:
            user_dict['profile_data'] = {}
        return user_dict
    return None

def save_user(user_data):
    """Save or update user data"""
    conn = get_db_connection()
    
    if 'profile_data' in user_data and isinstance(user_data['profile_data'], dict):
        profile_json = json.dumps(user_data['profile_data'])
    else:
        profile_json = user_data.get('profile_data', '{}')
    
    if 'id' in user_data:
        # Update existing user
        conn.execute('''
            UPDATE users 
            SET name = ?, profile_data = ?, questionnaire_completed = ?
            WHERE id = ?
        ''', (
            user_data['name'],
            profile_json,
            user_data.get('questionnaire_completed', False),
            user_data['id']
        ))
    else:
        # Create new user
        conn.execute('''
            INSERT INTO users (name, email, password_hash, date_of_birth, profile_data, questionnaire_completed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_data['name'],
            user_data['email'],
            user_data['password_hash'],
            user_data.get('date_of_birth'),
            profile_json,
            user_data.get('questionnaire_completed', False)
        ))
    
    conn.commit()
    conn.close()

def get_user_logs(user_id, days=30):
    """Get user's daily logs for the specified number of days"""
    conn = get_db_connection()
    logs = conn.execute('''
        SELECT * FROM daily_logs 
        WHERE user_id = ? 
        ORDER BY date DESC 
        LIMIT ?
    ''', (user_id, days)).fetchall()
    conn.close()
    
    return [dict(log) for log in logs]

def calculate_daily_score(log_data, user_profile):
    """Calculate a personalized daily score based on user's goals and log data"""
    score = 0
    max_score = 10
    
    goal = user_profile.get('goal', 'fat_loss')
    activity_level = user_profile.get('activity_level', 'moderately_active')
    
    # Sleep score (0-2.5 points)
    sleep_hours = float(log_data.get('sleep_hours', 0))
    if sleep_hours >= 7:
        score += 2.5
    elif sleep_hours >= 6:
        score += 2.0
    elif sleep_hours >= 5:
        score += 1.0
    
    # Water intake score (0-2 points)
    water_intake = log_data.get('water_intake', '')
    if water_intake == '> 3L':
        score += 2.0
    elif water_intake == '2-3L':
        score += 1.5
    elif water_intake == '1-2L':
        score += 1.0
    
    # Stress level score (0-2 points)
    stress_level = int(log_data.get('stress_level', 5))
    if stress_level <= 3:
        score += 2.0
    elif stress_level <= 5:
        score += 1.5
    elif stress_level <= 7:
        score += 1.0
    
    # Food quality score (0-2 points)
    food_log = log_data.get('food_log', '').lower()
    if any(word in food_log for word in ['salad', 'vegetables', 'protein', 'healthy', 'home cooked']):
        score += 2.0
    elif any(word in food_log for word in ['takeaway', 'fast food', 'pizza', 'junk']):
        score += 0.5
    else:
        score += 1.0
    
    # Exercise score (0-1.5 points) - adjusted based on goal
    workout = log_data.get('workout', '').lower()
    workout_duration = int(log_data.get('workout_duration', 0))
    
    if goal == 'muscle_gain':
        if 'strength' in workout or 'weights' in workout:
            score += 1.5
        elif workout_duration > 30:
            score += 1.0
    elif goal == 'fat_loss':
        if workout_duration > 45:
            score += 1.5
        elif workout_duration > 20:
            score += 1.0
    else:
        if workout_duration > 30:
            score += 1.5
        elif workout_duration > 15:
            score += 1.0
    
    return min(score, max_score)

def generate_ai_insights(user_profile, recent_logs):
    """Generate AI-powered insights based on user data"""
    if not openai.api_key:
        return [{
            'category': 'System',
            'icon': '💡',
            'message': 'AI insights will be available once OpenAI API is configured.',
            'action': 'Contact support for API setup assistance.'
        }]
    
    try:
        goal = user_profile.get('goal', 'fat_loss')
        activity_level = user_profile.get('activity_level', 'moderately_active')
        
        # Prepare context for AI
        context = f"""
        User Profile:
        - Goal: {goal}
        - Activity Level: {activity_level}
        - Recent logs: {len(recent_logs)} entries
        
        Recent patterns:
        """
        
        if recent_logs:
            avg_sleep = sum(float(log.get('sleep_hours', 0)) for log in recent_logs) / len(recent_logs)
            avg_stress = sum(int(log.get('stress_level', 5)) for log in recent_logs) / len(recent_logs)
            workout_days = len([log for log in recent_logs if log.get('workout_duration', 0) > 0])
            
            context += f"""
            - Average sleep: {avg_sleep:.1f} hours
            - Average stress: {avg_stress:.1f}/10
            - Workout days: {workout_days}/{len(recent_logs)}
            """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a fitness coach providing personalized insights. Give 2-3 specific, actionable insights based on the user's data. Format as JSON with category, icon, message, and action fields."
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            max_tokens=500
        )
        
        insights_text = response.choices[0].message.content
        insights = json.loads(insights_text)
        
        return insights if isinstance(insights, list) else [insights]
        
    except Exception as e:
        print(f"AI insights error: {e}")
        return [{
            'category': 'General',
            'icon': '💪',
            'message': 'Keep up the great work with your fitness journey!',
            'action': 'Continue logging daily for personalized insights.'
        }]

@app.route('/')
def landing_page():
    """Landing page with sign-up and login options"""
    if 'user_email' in session:
        user = get_user(session['user_email'])
        if user and user.get('questionnaire_completed'):
            return redirect(url_for('dashboard'))
        elif user:
            return redirect(url_for('questionnaire'))
    
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    """Handle user registration"""
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        date_of_birth = request.form.get('date_of_birth', '')
        
        # Validation
        if not all([name, email, password]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        if len(password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'})
        
        # Check if user exists
        if get_user(email):
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user_data = {
            'name': name,
            'email': email,
            'password_hash': password_hash,
            'date_of_birth': date_of_birth,
            'questionnaire_completed': False
        }
        
        save_user(user_data)
        session['user_email'] = email
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully!',
            'redirect': url_for('questionnaire')
        })
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'})

@app.route('/login', methods=['POST'])
def login():
    """Handle user login"""
    try:
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'})
        
        user = get_user(email)
        if not user:
            return jsonify({'success': False, 'message': 'Invalid email or password'})
        
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_email'] = email
            
            if user.get('questionnaire_completed'):
                redirect_url = url_for('dashboard')
            else:
                redirect_url = url_for('questionnaire')
            
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'redirect': redirect_url
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'})
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Login failed. Please try again.'})

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    """Handle the fitness questionnaire"""
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    if request.method == 'POST':
        try:
            user = get_user(session['user_email'])
            if not user:
                return jsonify({'success': False, 'message': 'User not found'})
            
            # Collect questionnaire data
            profile_data = {
                'goal': request.form.get('goal', 'fat_loss'),
                'current_weight': request.form.get('current_weight'),
                'target_weight': request.form.get('target_weight'),
                'height': request.form.get('height'),
                'sex': request.form.get('sex'),
                'activity_level': request.form.get('activity_level'),
                'exercise_routine': request.form.get('exercise_routine'),
                'motivation': request.form.get('motivation'),
                'motivation_level': request.form.get('motivation_level'),
                'dietary_preferences': request.form.get('dietary_preferences'),
                'health_conditions': request.form.get('health_conditions'),
                'questionnaire_completed': True,
                'completed_at': datetime.now().isoformat()
            }
            
            # Update user profile
            user['profile_data'].update(profile_data)
            user['questionnaire_completed'] = True
            save_user(user)
            
            return jsonify({
                'success': True,
                'message': 'Profile completed successfully!',
                'redirect': url_for('dashboard')
            })
            
        except Exception as e:
            print(f"Questionnaire error: {e}")
            return jsonify({'success': False, 'message': 'Failed to save questionnaire'})
    
    return render_template('questionnaire.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard with personalized content"""
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))
    
    if not user.get('questionnaire_completed'):
        return redirect(url_for('questionnaire'))
    
    try:
        # Get user's recent logs
        recent_logs = get_user_logs(user['id'], 30)
        
        # Calculate user statistics
        user_stats = {
            'total_logs': len(recent_logs),
            'streak_days': calculate_streak(recent_logs),
            'days_active': len([log for log in recent_logs if log.get('workout_duration', 0) > 0]),
            'avg_score': calculate_average_score(recent_logs)
        }
        
        # Generate personalized content
        personalized_content = generate_personalized_dashboard_content(
            user, recent_logs, user_stats
        )
        
        # Get latest score and components
        latest_log = recent_logs[0] if recent_logs else None
        latest_score = latest_log.get('score') if latest_log else None
        
        # Generate AI insights
        ai_insights = generate_ai_insights(user['profile_data'], recent_logs[:7])
        
        # Prepare dashboard data
        dashboard_data = {
            'user': user,
            'user_stats': user_stats,
            'latest_score': latest_score,
            'recent_logs': recent_logs[:7],
            'ai_insights': ai_insights,
            'personalized_content': personalized_content,
            'score_history': prepare_score_history(recent_logs)
        }
        
        return render_template('dashboard.html', **dashboard_data)
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('Error loading dashboard. Please try again.')
        return render_template('dashboard.html', user=user, error=True)

@app.route('/daily-log', methods=['GET', 'POST'])
def daily_log():
    """Handle daily logging"""
    if 'user_email' not in session:
        return redirect(url_for('landing_page'))
    
    user = get_user(session['user_email'])
    if not user:
        return redirect(url_for('landing_page'))
    
    if request.method == 'POST':
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            log_data = {
                'weight': request.form.get('weight'),
                'sleep_hours': request.form.get('sleep_hours'),
                'water_intake': request.form.get('water_intake'),
                'stress_level': request.form.get('stress_level'),
                'mood': request.form.get('mood'),
                'food_log': request.form.get('food_log'),
                'workout': request.form.get('workout'),
                'workout_duration': request.form.get('workout_duration', 0),
                'notes': request.form.get('notes')
            }
            
            # Calculate daily score
            score = calculate_daily_score(log_data, user['profile_data'])
            log_data['score'] = score
            
            # Save to database
            conn = get_db_connection()
            conn.execute('''
                INSERT OR REPLACE INTO daily_logs 
                (user_id, date, weight, sleep_hours, water_intake, stress_level, 
                 mood, food_log, workout, workout_duration, notes, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user['id'], today, log_data['weight'], log_data['sleep_hours'],
                log_data['water_intake'], log_data['stress_level'], log_data['mood'],
                log_data['food_log'], log_data['workout'], log_data['workout_duration'],
                log_data['notes'], log_data['score']
            ))
            conn.commit()
            conn.close()
            
            flash(f'Daily log saved! Your score today: {score:.1f}/10')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"Daily log error: {e}")
            flash('Error saving daily log. Please try again.')
    
    # Get today's existing log if any
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    existing_log = conn.execute(
        'SELECT * FROM daily_logs WHERE user_id = ? AND date = ?',
        (user['id'], today)
    ).fetchone()
    conn.close()
    
    return render_template('daily-log.html', 
                         user=user, 
                         existing_log=dict(existing_log) if existing_log else None)

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """API endpoint for dashboard data (for mobile app)"""
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = get_user(session['user_email'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        recent_logs = get_user_logs(user['id'], 30)
        user_stats = {
            'total_logs': len(recent_logs),
            'streak_days': calculate_streak(recent_logs),
            'days_active': len([log for log in recent_logs if log.get('workout_duration', 0) > 0]),
            'avg_score': calculate_average_score(recent_logs)
        }
        
        personalized_content = generate_personalized_dashboard_content(
            user, recent_logs, user_stats
        )
        
        ai_insights = generate_ai_insights(user['profile_data'], recent_logs[:7])
        
        return jsonify({
            'user': {
                'name': user['name'],
                'email': user['email'],
                'profile_data': user['profile_data']
            },
            'user_stats': user_stats,
            'latest_score': recent_logs[0].get('score') if recent_logs else None,
            'ai_insights': ai_insights,
            'personalized_content': personalized_content,
            'score_history': prepare_score_history(recent_logs)
        })
        
    except Exception as e:
        print(f"API dashboard error: {e}")
        return jsonify({'error': 'Failed to load dashboard data'}), 500

@app.route('/api/health-connect', methods=['POST'])
def api_health_connect():
    """API endpoint for health data sync from mobile apps"""
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = get_user(session['user_email'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        health_data = request.get_json()
        platform = health_data.get('platform')  # 'apple' or 'google'
        data = health_data.get('data', {})
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Save health data
        conn = get_db_connection()
        conn.execute('''
            INSERT OR REPLACE INTO health_data 
            (user_id, date, steps, heart_rate, calories_burned, active_minutes, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user['id'], today,
            data.get('steps', 0),
            data.get('heart_rate'),
            data.get('calories', 0),
            data.get('active_minutes', 0),
            platform
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Health data synced successfully'})
        
    except Exception as e:
        print(f"Health connect error: {e}")
        return jsonify({'error': 'Failed to sync health data'}), 500

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    flash('You have been logged out successfully.')
    return redirect(url_for('landing_page'))

# Utility functions
def calculate_streak(logs):
    """Calculate current streak of consecutive days with logs"""
    if not logs:
        return 0
    
    streak = 0
    current_date = datetime.now().date()
    
    for log in logs:
        log_date = datetime.strptime(log['date'], '%Y-%m-%d').date()
        if log_date == current_date:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak

def calculate_average_score(logs):
    """Calculate average score from recent logs"""
    if not logs:
        return 0
    
    scores = [log.get('score', 0) for log in logs if log.get('score')]
    return sum(scores) / len(scores) if scores else 0

def prepare_score_history(logs):
    """Prepare score history data for charts"""
    if not logs:
        return []
    
    history = []
    for log in reversed(logs[-14:]):  # Last 14 days
        if log.get('score'):
            history.append({
                'date': log['date'],
                'score': log['score']
            })
    
    return history

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
