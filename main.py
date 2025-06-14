
print("\n🧠 Welcome to your Fitness Tracker!\nLet's learn a bit about you...\n")

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



# Show basic health summary (no AI required)
print("\n🔍 Health Summary:\n")
print(f"Goal: {user_data['goal'].title()}")
print(f"Sleep: {user_data['sleep_hours']} hours (recommendation: 7-9 hours)")
print(f"Steps: {user_data['steps']:,} (recommendation: 8,000+ steps)")
print(f"Calories: {user_data['calories_intake']} eaten vs {user_data['target_calories']} target")
print(f"Energy level: {user_data['energy_level'].title()}")
if user_data['cycle_phase'] != 'none':
    print(f"Menstrual phase: {user_data['cycle_phase'].title()}")
print("\n✅ Data collected successfully! Your fitness tracker is working.")
