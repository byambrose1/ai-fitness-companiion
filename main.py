from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Get all form data
    user_data = {
        'goal': request.form['goal'].strip().lower(),
        'age': int(request.form['age']),
        'sex': request.form['sex'].strip().lower(),
        'height': float(request.form['height']),
        'weight': float(request.form['weight']),
        'sleep_hours': float(request.form['sleep_hours']),
        'steps': int(request.form['steps']),
        'energy_level': request.form['energy_level'].strip().lower(),
        'water_litres': float(request.form['water_litres']),
        'protein_intake': int(request.form['protein_intake']),
        'carbs_intake': int(request.form['carbs_intake']),
        'fats_intake': int(request.form['fats_intake']),
        'calories_intake': int(request.form['calories_intake']),
        'target_calories': int(request.form['target_calories']),
        'cycle_phase': request.form['cycle_phase'].strip().lower()
    }

    return render_template('results.html', data=user_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)