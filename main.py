import openai
import os

# Get API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Ask user for input
print("🧠 Welcome to your AI Fitness Coach!\nPlease answer the following:")

goal = input("What is your goal? (fat_loss or weight_gain): ").strip().lower()
sleep_hours = float(input("How many hours did you sleep last night?: "))
protein_intake = int(input("How much protein did you eat yesterday (grams)?: "))
target_protein = int(input("What is your target protein intake (grams)?: "))
steps = int(input("How many steps did you walk yesterday?: "))
weight_change = float(input("How much did your weight change this week? (kg, e.g. -0.5 or 1.2): "))
energy_level = input("How's your energy today? (low / ok / high): ").strip().lower()

user_data = {
    "goal": goal,
    "sleep_hours": sleep_hours,
    "protein_intake": protein_intake,
    "target_protein": target_protein,
    "steps": steps,
    "weight_change": weight_change,
    "energy_level": energy_level
}

# Generate the AI prompt
def generate_prompt(data):
    return f"""
You are a fitness and health AI coach. A user trying to {data['goal']} has the following stats:
- Sleep: {data['sleep_hours']} hours
- Protein: {data['protein_intake']}g (target is {data['target_protein']}g)
- Steps: {data['steps']}
- Weight change this week: {data['weight_change']} kg
- Energy level: {data['energy_level']}

Give the user a supportive daily feedback report:
1. Why they might feel tired or have gained/lost weight.
2. Two actionable, helpful tips for today.
Keep it friendly, short, and motivational.
"""

# Get AI feedback
def get_ai_feedback(user_data):
    prompt = generate_prompt(user_data)

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response['choices'][0]['message']['content']

# Print the feedback
print("\n🔍 Your AI Feedback:\n")
print(get_ai_feedback(user_data))