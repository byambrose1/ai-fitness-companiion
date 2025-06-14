
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Get all form data
    user_data = {
        # Personal Info
        'sex': request.form.get('sex', '').strip().lower(),
        'age': request.form.get('age', 0, type=int),
        'height': request.form.get('height', 0.0, type=float),
        'weight': request.form.get('weight', 0.0, type=float),
        'weight_change': request.form.get('weight_change', '').strip().lower(),
        'goal': request.form.get('goal', '').strip().lower(),
        
        # Journey
        'duration': request.form.get('duration', '').strip().lower(),
        'tried': request.form.getlist('tried'),  # Multiple checkboxes
        'confidence': request.form.get('confidence', 0, type=int),
        'struggle': request.form.get('struggle', '').strip().lower(),
        
        # Nutrition
        'track_food': request.form.get('track_food', '').strip().lower(),
        'calories': request.form.get('calories', 0, type=int),
        'protein': request.form.get('protein', 0, type=int),
        'carbs': request.form.get('carbs', 0, type=int),
        'fats': request.form.get('fats', 0, type=int),
        'diet': request.form.get('diet', '').strip(),
        
        # Recovery
        'sleep': request.form.get('sleep', 0.0, type=float),
        'energy': request.form.get('energy', '').strip().lower(),
        'cycle': request.form.get('cycle', '').strip().lower(),
        
        # Activity
        'activity': request.form.get('activity', '').strip().lower(),
        'exercise': request.form.get('exercise', '').strip().lower(),
        'exercise_type': request.form.get('exercise_type', '').strip(),
        
        # Final question
        'wish': request.form.get('wish', '').strip()
    }

    return render_template('results.html', data=user_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
