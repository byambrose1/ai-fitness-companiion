
from flask import Flask, request, render_template_string
from datetime import datetime

app = Flask(__name__)

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

        # Extract all form data
        email = data.get("email")
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
            <title>Your Personalised Fitness Profile</title>
            <style>
                * {
                    box-sizing: border-box;
                }
                
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                
                .container {
                    background: white;
                    padding: 2em;
                    border-radius: 15px;
                    max-width: 900px;
                    margin: 0 auto;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }
                
                .summary-item { 
                    margin: 12px 0; 
                    padding: 15px; 
                    background: linear-gradient(145deg, #f8f9fa, #e9ecef);
                    border-radius: 10px; 
                    border-left: 5px solid #667eea;
                }
                
                .button { 
                    display: inline-block; 
                    padding: 15px 30px; 
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white; 
                    text-decoration: none; 
                    border-radius: 10px; 
                    margin-top: 30px; 
                    text-align: center;
                    width: 100%;
                    box-sizing: border-box;
                    font-weight: 600;
                    transition: transform 0.2s ease;
                }
                
                .button:hover { 
                    transform: translateY(-2px);
                }
                
                h1 { 
                    text-align: center; 
                    color: #333; 
                    margin-bottom: 30px;
                }
                
                h2 { 
                    color: #667eea; 
                    margin-top: 30px; 
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 10px;
                }
                
                .ai-section {
                    background: linear-gradient(145deg, #e3f2fd, #bbdefb);
                    padding: 20px;
                    border-radius: 10px;
                    margin: 25px 0;
                    text-align: center;
                    border-left: 5px solid #2196f3;
                }
                
                .highlight {
                    background: linear-gradient(145deg, #fff3e0, #ffe0b2);
                    border-left-color: #ff9800;
                }
                
                @media (max-width: 768px) {
                    .container {
                        padding: 1.5em;
                        margin: 0.5em;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎉 Your Personalised Fitness Profile</h1>
                <p style="text-align: center; font-size: 18px; color: #666;">Thank you for sharing your detailed information. Here's your comprehensive summary:</p>

                <h2>👤 Personal Information</h2>
                <div class="summary-item"><strong>Email:</strong> {{ email }}</div>
                <div class="summary-item"><strong>Age:</strong> {{ age }} years old</div>
                <div class="summary-item"><strong>Biological Sex:</strong> {{ gender|title }}</div>
                <div class="summary-item"><strong>Height:</strong> {{ height }} cm</div>
                <div class="summary-item"><strong>Current Weight:</strong> {{ weight }} kg</div>
                {% if goal_weight %}
                <div class="summary-item"><strong>Goal Weight:</strong> {{ goal_weight }} kg</div>
                {% endif %}

                <h2>🎯 Goals & Motivation</h2>
                <div class="summary-item highlight"><strong>Primary Goal:</strong> {{ goal|replace('_', ' ')|title }}</div>
                {% if goal_reason %}
                <div class="summary-item"><strong>Goal Reason:</strong> {{ goal_reason|replace('_', ' ')|title }}</div>
                {% endif %}
                <div class="summary-item"><strong>Your Motivation:</strong> {{ motivation }}</div>

                <h2>💭 Mental & Emotional State</h2>
                <div class="summary-item"><strong>Current Mental State:</strong> {{ mental_state }}</div>
                <div class="summary-item"><strong>Motivation Level:</strong> {{ motivation_level }}/10</div>
                <div class="summary-item"><strong>Mood:</strong> 
                    {% if mood_custom %}
                        {{ mood_custom }}
                    {% else %}
                        {{ mood|title }}
                    {% endif %}
                </div>

                <h2>🏥 Health Information</h2>
                <div class="summary-item"><strong>Medications:</strong> 
                    {% if medications == 'yes' and medication_list %}
                        Yes - {{ medication_list }}
                    {% elif medications == 'yes' %}
                        Yes
                    {% else %}
                        No
                    {% endif %}
                </div>
                {% if health_conditions %}
                <div class="summary-item"><strong>Health Conditions:</strong> {{ health_conditions }}</div>
                {% endif %}
                {% if menstrual_cycle and menstrual_cycle != '' %}
                <div class="summary-item"><strong>Menstrual Status:</strong> {{ menstrual_cycle|replace('_', ' ')|title }}</div>
                {% endif %}

                <h2>😴 Sleep & Recovery</h2>
                <div class="summary-item"><strong>Sleep Hours:</strong> {{ sleep_hours }} hours per night</div>
                <div class="summary-item"><strong>Waking Feeling:</strong> {{ waking_feeling|title }}</div>

                <h2>🍽️ Nutrition</h2>
                <div class="summary-item"><strong>Protein Sources:</strong> {{ protein_sources }}</div>
                <div class="summary-item"><strong>Meals Per Day:</strong> {{ meals_per_day }}</div>
                <div class="summary-item"><strong>Water Intake:</strong> {{ water_intake|replace('_', ' ')|title }}</div>
                <div class="summary-item"><strong>Eating Habits:</strong> {{ eating_habits|replace('_', ' ')|title }}</div>

                <h2>🏃‍♀️ Activity & Exercise</h2>
                <div class="summary-item"><strong>Activity Level:</strong> {{ activity_level|replace('_', ' ')|title }}</div>
                <div class="summary-item"><strong>Exercise Details:</strong> {{ exercise_details }}</div>
                {% if wearables and wearables != 'none' %}
                <div class="summary-item"><strong>Fitness Wearables:</strong> {{ wearables|replace('_', ' ')|title }}</div>
                {% endif %}

                <h2>📊 Body & Progress</h2>
                <div class="summary-item"><strong>Recent Weight Changes:</strong> {{ weight_changes|replace('_', ' ')|title }}</div>
                <div class="summary-item"><strong>How You Feel in Your Body:</strong> {{ body_feeling }}</div>
                {% if weekly_weigh_in %}
                <div class="summary-item"><strong>Weekly Weight Check-ins:</strong> {{ weekly_weigh_in|title }}</div>
                {% endif %}

                <h2>🌈 Lifestyle</h2>
                <div class="summary-item"><strong>Stress Level:</strong> {{ stress_level }}/10</div>
                <div class="summary-item"><strong>Support System:</strong> {{ support_system|title }}
                    {% if support_explanation %}
                        - {{ support_explanation }}
                    {% endif %}
                </div>

                {% if ai_consent == 'yes' %}
                <div class="ai-section">
                    <h2>🤖 AI Personalised Recommendations</h2>
                    <p><strong>✨ Based on your comprehensive profile, here are your personalised tips:</strong></p>
                    
                    <div style="text-align: left; margin: 20px 0;">
                        <div class="summary-item">
                            <strong>🎯 Goal-Specific Tip:</strong> 
                            {% if goal == 'fat_loss' %}
                                Focus on creating a moderate calorie deficit through a combination of nutrition and exercise. With {{ sleep_hours }} hours of sleep, ensure you're getting adequate rest as poor sleep can interfere with fat loss.
                            {% elif goal == 'muscle_gain' %}
                                Prioritise protein intake (aim for 1.6-2.2g per kg body weight) and progressive overload in your training. Your current protein sources look good - consider timing protein around your workouts.
                            {% elif goal == 'general_health' %}
                                Focus on consistency over intensity. Your {{ activity_level|replace('_', ' ') }} activity level is a great foundation - gradually increase movement and maintain your {{ eating_habits|replace('_', ' ') }} approach.
                            {% else %}
                                Exercise is fantastic for mental wellbeing. Consider activities you enjoy and can sustain long-term, especially given your current motivation level of {{ motivation_level }}/10.
                            {% endif %}
                        </div>
                        
                        <div class="summary-item">
                            <strong>😴 Sleep & Recovery:</strong>
                            {% if sleep_hours|int < 7 %}
                                Aim to increase your sleep to 7-9 hours per night. Quality sleep is crucial for {{ goal|replace('_', ' ') }} and will help improve how you feel when waking up.
                            {% elif sleep_hours|int > 9 %}
                                Your sleep duration is good, but feeling {{ waking_feeling }} when waking suggests looking at sleep quality. Consider a consistent bedtime routine.
                            {% else %}
                                Your {{ sleep_hours }} hours of sleep is in the optimal range. Focus on sleep quality if you're still feeling {{ waking_feeling }} upon waking.
                            {% endif %}
                        </div>
                        
                        <div class="summary-item">
                            <strong>🧠 Mental Wellbeing:</strong>
                            With a stress level of {{ stress_level }}/10 and motivation at {{ motivation_level }}/10, 
                            {% if stress_level|int > 6 %}
                                consider stress management techniques like meditation, yoga, or regular walks. High stress can impact your {{ goal|replace('_', ' ') }} goals.
                            {% elif motivation_level|int < 5 %}
                                start with small, achievable goals to build momentum. Your {{ support_system }} support system will be valuable in maintaining consistency.
                            {% else %}
                                you're in a good mental space to pursue your goals. Use this positive momentum to establish sustainable habits.
                            {% endif %}
                        </div>
                    </div>
                    
                    <p><em>💡 Remember: Small, consistent changes lead to lasting results. Focus on one area at a time!</em></p>
                </div>
                {% else %}
                <div style="background: #f0f0f0; padding: 20px; border-radius: 10px; margin: 25px 0; text-align: center;">
                    <p><strong>✅ Profile Complete!</strong></p>
                    <p>Your comprehensive fitness profile has been created successfully.</p>
                </div>
                {% endif %}
                
                <a href="/" class="button">📝 Update Your Profile</a>
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
