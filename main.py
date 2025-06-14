
import openai
import os

# Get API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

print("\n🧠 Welcome to your AI Fitness Coach!\nLet's learn a bit about you...\n")

# Collect user input
goal = input("🎯 Goal (fat_loss / weight_gain): ").strip().lower()
age = int(input("🎂 Age: "))
sex = input("🧬 Biological Sex (male / female): ").strip().lower()
height = float(input("📏 Height in cm: "))
weight = float(input("⚖️ Current weight in kg: "))
sleep_hours = float(input("😴 Hours of sleep last night: "))
steps = int(input("🚶 Steps walked yesterday: "))
energy_level = input("⚡ Energy level today (low / ok / high): ").strip().lower()
water_litres = float(input("💧 Water intake yesterday (litres): "))
protein_intake = int(input("🍗 Protein eaten yesterday (grams): "))
carbs_intake = int(input("🍞 Carbs eaten yesterday (grams): "))
fats_intake = int(input("🥑 Fats eaten yesterday (grams): "))
calories_intake = int(input("🔥 Total calories eaten yesterday: "))
target_calories = int(input("🎯 Target daily calories: "))
cycle_phase = input("🩸 Menstrual cycle phase? (none / follicular / ovulation / luteal / period): ").strip().lower()

# Structure the user data
user_data = {
    "goal": goal,
    "age": age,
    "sex": sex,
    "height": height,
    "weight": weight,
    "sleep_hours": sleep_hours,
    "steps": steps,
    "energy_level": energy_level,
    "water_litres": water_litres,
    "protein_intake": protein_intake,
    "carbs_intake": carbs_intake,
    "fats_intake": fats_intake,
    "calories_intake": calories_intake,
    "target_calories": target_calories,
    "cycle_phase": cycle_phase
}

# Prompt to guide AI feedback
def generate_prompt(data):
    return f"""
You are a compassionate but realistic female fitness and health AI coach. A user is trying to achieve {data['goal']} and has submitted the following:

- Age: {data['age']} | Sex: {data['sex']}
- Height: {data['height']} cm | Weight: {data['weight']} kg
- Sleep: {data['sleep_hours']} hours
- Steps: {data['steps']}
- Energy: {data['energy_level']}
- Water: {data['water_litres']} litres
- Protein: {data['protein_intake']}g
- Carbs: {data['carbs_intake']}g
- Fats: {data['fats_intake']}g
- Calories: {data['calories_intake']} kcal (Target: {data['target_calories']} kcal)
- Menstrual phase: {data['cycle_phase']}

Give back:
1. A short, motivational summary (with context on weight, energy, period, etc.)
2. 2–3 actionable daily tips (adjustments or reminders)
3. Tone: supportive, friendly, honest

Respond clearly and briefly. No emojis.
"""

# Get AI feedback from OpenAI
def get_ai_feedback(user_data):
    prompt = generate_prompt(user_data)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# Show the AI feedback
print("\n🔍 AI Feedback:\n")
print(get_ai_feedback(user_data))
