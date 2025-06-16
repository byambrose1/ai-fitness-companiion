
from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        data = request.form

        # Extracting new form data
        email = data.get("email")
        dob = data.get("dob")
        gender = data.get("gender")
        cycle = data.get("cycle") if gender == "female" else "N/A"
        goal = data.get("goal")
        motivation = data.get("motivation")
        mood = data.get("mood")
        medication = data.get("medication")
        food_habits = data.get("foodHabits")
        activity = data.get("activity")
        protein = data.get("protein")
        sleep = data.get("sleep")
        weight_change = data.get("weightChange")

        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Fitness Assistant - Your Profile</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    background-color: #f4f4f4;
                }
                .container {
                    background: white;
                    padding: 2em;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                .summary-item { 
                    margin: 10px 0; 
                    padding: 12px; 
                    background: #f8f9fa; 
                    border-radius: 5px; 
                    border-left: 4px solid #28a745;
                }
                .button { 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background: #28a745; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin-top: 20px; 
                    text-align: center;
                    width: 100%;
                    box-sizing: border-box;
                }
                .button:hover { background: #218838; }
                h2 { text-align: center; color: #333; }
                h3 { color: #28a745; margin-top: 25px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>✅ Your Personalised Fitness Profile</h2>
                <p style="text-align: center;">Thank you for sharing your details. Here's your summary:</p>

                <h3>👤 Personal Information</h3>
                <div class="summary-item"><strong>Email:</strong> {{ email }}</div>
                <div class="summary-item"><strong>Date of Birth:</strong> {{ dob }}</div>
                <div class="summary-item"><strong>Gender:</strong> {{ gender|title }}</div>
                {% if cycle != 'N/A' %}
                <div class="summary-item"><strong>Menstrual Status:</strong> {{ cycle|title }}</div>
                {% endif %}

                <h3>🎯 Your Goals & Motivation</h3>
                <div class="summary-item"><strong>Main Goal:</strong> {{ goal|replace('_', ' ')|title }}</div>
                <div class="summary-item"><strong>Your Motivation:</strong> {{ motivation }}</div>
                <div class="summary-item"><strong>Current Mood:</strong> {{ mood }}</div>

                <h3>🏥 Health Information</h3>
                {% if medication %}
                <div class="summary-item"><strong>Medication/Health Conditions:</strong> {{ medication }}</div>
                {% endif %}
                <div class="summary-item"><strong>Recent Weight Changes:</strong> {{ weight_change|replace('_', ' ')|title }}</div>

                <h3>🍽️ Nutrition & Lifestyle</h3>
                <div class="summary-item"><strong>Food Habits:</strong> {{ food_habits|replace('_', ' ')|title }}</div>
                <div class="summary-item"><strong>Daily Protein Intake:</strong> {{ protein }}</div>
                <div class="summary-item"><strong>Sleep Hours:</strong> {{ sleep }} hours per night</div>

                <h3>🏃‍♀️ Activity Level</h3>
                <div class="summary-item"><strong>Daily Activity:</strong> {{ activity }}</div>

                <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin-top: 25px; text-align: center;">
                    <p><strong>✅ Profile Complete!</strong></p>
                    <p>🧠 Your personalised fitness recommendations are being prepared.</p>
                </div>
                
                <a href="/" class="button">📝 Update Your Profile</a>
            </div>
        </body>
        </html>
        """, email=email, dob=dob, gender=gender, cycle=cycle, goal=goal,
           motivation=motivation, mood=mood, medication=medication,
           food_habits=food_habits, activity=activity, protein=protein,
           sleep=sleep, weight_change=weight_change)

    return open("templates/index.html").read()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
