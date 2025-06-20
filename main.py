
from flask import Flask, request, render_template_string, jsonify, session
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production

# Simple in-memory storage (replace with database in production)
users_data = {}

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        data = request.form
        
        # Calculate age from date of birth
        dob = data.get("dob")
        if dob:
            birth_date = datetime.strptime(dob, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        else:
            age = "Not provided"
            
        # Age validation
        if isinstance(age, int) and age < 18:
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Age Restriction</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
                    .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    .error { color: #ff6b6b; font-size: 18px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>⚠️ Age Restriction</h2>
                    <div class="error">You must be 18 or older to use this service.</div>
                    <a href="/" style="text-decoration: none; background: #667eea; color: white; padding: 10px 20px; border-radius: 5px;">← Go Back</a>
                </div>
            </body>
            </html>
            """)

        # Store user data (in production, save to database)
        email = data.get("email")
        user_profile = {
            'email': email,
            'dob': dob,
            'age': age,
            'created_at': datetime.now().isoformat(),
            'profile_data': dict(data),
            'daily_logs': [],
            'weekly_checkins': []
        }
        
        # Simple storage by email (replace with proper user management)
        users_data[email] = user_profile

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
            <style>
                * { box-sizing: border-box; }
                
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0; padding: 20px;
                    background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%);
                    min-height: 100vh;
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
                <h1>✨ Welcome to Your Fitness Journey</h1>
                <div style="text-align: center; margin-bottom: 30px;">
                    <span class="success-badge">✅ Profile Created Successfully</span>
                </div>
                
                <p style="text-align: center; font-size: 18px; color: #2d5a3d; margin-bottom: 30px;">
                    Thank you for sharing your information, {{ email.split('@')[0]|title }}! Your personalised wellness companion is ready.
                </p>

                <h2>👤 Your Profile Summary</h2>
                <div class="summary-item"><strong>Email:</strong> {{ email }}</div>
                <div class="summary-item"><strong>Age:</strong> {{ age }} years old</div>
                <div class="summary-item"><strong>Biological Sex:</strong> {{ gender|title }}</div>
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
        email=email, age=age, gender=gender, height=height, weight=weight, 
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
    if not email or email not in users_data:
        return "User not found. Please complete your profile first."
    
    user = users_data[email]
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
            <h1>🌟 Welcome back, {{ user.email.split('@')[0]|title }}!</h1>
            
            <div class="reminder">
                <p>💚 <strong>Daily Reminder:</strong> You're doing great! Remember to log your meals and movement today.</p>
            </div>
            
            <div class="dashboard-grid">
                <div class="card">
                    <h3>📊 Today's Scores</h3>
                    <div class="score">N/A</div>
                    <p>Complete your daily log to see your scores</p>
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
            <div style="text-align: center;">
                <a href="/daily-log?email={{ user.email }}" class="button">📝 Daily Log</a>
                <a href="/weekly-checkin?email={{ user.email }}" class="button">📅 Weekly Check-in</a>
                <a href="/ai-chat?email={{ user.email }}" class="button">🤖 Ask AI</a>
                <a href="/" class="button">⚙️ Update Profile</a>
            </div>
        </div>
    </body>
    </html>
    """, user=user)

@app.route("/daily-log")
def daily_log():
    email = request.args.get('email')
    if not email:
        return "Please provide email parameter"
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en-GB">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Log</title>
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
            <h1>📝 Daily Log</h1>
            <p style="text-align: center; color: #666;">Track your daily wellness journey</p>
            
            <form method="POST" action="/save-daily-log">
                <input type="hidden" name="email" value="{{ email }}">
                <input type="hidden" name="date" value="{{ today }}">
                
                <label for="food_log">🍽️ What did you eat today?</label>
                <textarea name="food_log" placeholder="E.g., oats with berries for breakfast, chicken salad for lunch..." rows="3"></textarea>
                
                <label for="workout">🏃‍♀️ Workout Type:</label>
                <select name="workout">
                    <option value="">-- Select --</option>
                    <option value="cardio">Cardio</option>
                    <option value="strength">Strength Training</option>
                    <option value="yoga">Yoga</option>
                    <option value="walking">Walking</option>
                    <option value="other">Other</option>
                    <option value="rest">Rest Day</option>
                </select>
                
                <label for="workout_duration">⏱️ Workout Duration (minutes):</label>
                <input type="number" name="workout_duration" min="0" max="300">
                
                <label for="weight">⚖️ Weight (kg) - Optional:</label>
                <input type="number" name="weight" step="0.1" min="30" max="300">
                
                <label for="mood">😊 Mood Today:</label>
                <select name="mood">
                    <option value="">-- Select --</option>
                    <option value="excellent">Excellent</option>
                    <option value="good">Good</option>
                    <option value="okay">Okay</option>
                    <option value="low">Low</option>
                    <option value="stressed">Stressed</option>
                </select>
                
                <label for="sleep_hours">😴 Hours of Sleep:</label>
                <input type="number" name="sleep_hours" step="0.5" min="0" max="24">
                
                <label for="stress_level">😰 Stress Level (1-10):</label>
                <input type="range" name="stress_level" min="1" max="10" value="5">
                
                <label for="water_intake">💧 Water Intake:</label>
                <select name="water_intake">
                    <option value="">-- Select --</option>
                    <option value="low">Less than 1L</option>
                    <option value="moderate">1-2L</option>
                    <option value="good">2-3L</option>
                    <option value="excellent">3L+</option>
                </select>
                
                <label for="notes">💭 Additional Notes:</label>
                <textarea name="notes" placeholder="How are you feeling today? Any observations?" rows="2"></textarea>
                
                <button type="submit" class="button">💾 Save Today's Log</button>
            </form>
            
            <div style="text-align: center; margin-top: 20px;">
                <a href="/dashboard?email={{ email }}" style="color: #2d5a3d;">← Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """, email=email, today=datetime.now().strftime("%Y-%m-%d"))

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
        'notes': request.form.get('notes')
    }
    
    users_data[email]['daily_logs'].append(log_entry)
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Log Saved</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #A8E6CF 0%, #88D8A3 100%); }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; }
            .success { color: #00b894; font-size: 18px; margin: 20px 0; }
            .button { background: #A8E6CF; color: #2d5a3d; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>✅ Daily Log Saved!</h2>
            <div class="success">Your daily log has been recorded successfully.</div>
            <p>Keep up the great work! Consistency is key to reaching your goals.</p>
            <a href="/dashboard?email={{ email }}" class="button">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """, email=email)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
