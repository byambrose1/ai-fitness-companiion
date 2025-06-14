
from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        data = request.form

        # Extracting form data
        sex = data.get("sex")
        age = data.get("age")
        height = data.get("height")
        weight = data.get("weight")
        weight_change = data.get("weight_change")
        goal = data.get("goal")
        duration = data.get("duration")
        tried = request.form.getlist("tried")
        confidence = data.get("confidence")
        struggle = data.get("struggle")
        track_food = data.get("track_food")
        calories = data.get("calories")
        protein = data.get("protein")
        carbs = data.get("carbs")
        fats = data.get("fats")
        diet = data.get("diet")
        sleep = data.get("sleep")
        energy = data.get("energy")
        cycle = data.get("cycle") if sex == "Female" else "N/A"
        activity = data.get("activity")
        exercise = data.get("exercise")
        exercise_type = data.get("exercise_type")
        wish = data.get("wish")

        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Fitness Check-In Results</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .summary-item { margin: 10px 0; padding: 8px; background: #f5f5f5; border-radius: 4px; }
                .button { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h2>✅ Thank You for Your Check-In!</h2>
            <p>Your comprehensive fitness profile has been submitted. Here's your summary:</p>

            <h3>🧍 Personal Information</h3>
            <div class="summary-item"><strong>Sex:</strong> {{ sex }}</div>
            <div class="summary-item"><strong>Age:</strong> {{ age }} years old</div>
            <div class="summary-item"><strong>Height:</strong> {{ height }} cm</div>
            <div class="summary-item"><strong>Current Weight:</strong> {{ weight }} kg</div>
            <div class="summary-item"><strong>Weight Change:</strong> {{ weight_change }}</div>
            <div class="summary-item"><strong>Main Goal:</strong> {{ goal }}</div>

            <h3>💭 Your Journey</h3>
            <div class="summary-item"><strong>Duration:</strong> {{ duration }}</div>
            <div class="summary-item"><strong>What You've Tried:</strong> {{ tried|join(', ') if tried else 'Nothing yet' }}</div>
            <div class="summary-item"><strong>Confidence Level:</strong> {{ confidence }}/5</div>
            <div class="summary-item"><strong>Biggest Struggle:</strong> {{ struggle }}</div>

            <h3>🍽 Nutrition</h3>
            <div class="summary-item"><strong>Track Food:</strong> {{ track_food }}</div>
            <div class="summary-item"><strong>Daily Calories:</strong> {{ calories }} kcal</div>
            <div class="summary-item"><strong>Daily Protein:</strong> {{ protein }} g</div>
            <div class="summary-item"><strong>Daily Carbs:</strong> {{ carbs }} g</div>
            <div class="summary-item"><strong>Daily Fats:</strong> {{ fats }} g</div>
            <div class="summary-item"><strong>Special Diet:</strong> {{ diet or 'None' }}</div>

            <h3>🛌 Recovery & Activity</h3>
            <div class="summary-item"><strong>Sleep Last Night:</strong> {{ sleep }} hours</div>
            <div class="summary-item"><strong>Energy Today:</strong> {{ energy }}</div>
            <div class="summary-item"><strong>Cycle Phase:</strong> {{ cycle }}</div>
            <div class="summary-item"><strong>Activity Level:</strong> {{ activity }}</div>
            <div class="summary-item"><strong>Exercise Regularly:</strong> {{ exercise }}</div>
            <div class="summary-item"><strong>Exercise Type:</strong> {{ exercise_type or 'None specified' }}</div>

            {% if wish %}
            <h3>💭 Your Wish</h3>
            <div class="summary-item">{{ wish }}</div>
            {% endif %}

            <p>✅ Your responses will help personalize your fitness journey.</p>
            <p>🧠 <strong>Coming Soon:</strong> Smart AI tips, habit tracking, and goal-based coaching.</p>
            
            <a href="/" class="button">📝 Submit Another Check-In</a>
        </body>
        </html>
        """, sex=sex, age=age, height=height, weight=weight, weight_change=weight_change,
           goal=goal, duration=duration, tried=tried, confidence=confidence,
           struggle=struggle, track_food=track_food, calories=calories,
           protein=protein, carbs=carbs, fats=fats, diet=diet, sleep=sleep,
           energy=energy, cycle=cycle, activity=activity, exercise=exercise,
           exercise_type=exercise_type, wish=wish)

    return open("templates/index.html").read()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
