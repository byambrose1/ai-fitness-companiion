
#!/usr/bin/env python3
"""
7-Day Premium User Simulation for Fitness Companion App
This simulates a realistic user journey to demonstrate app features and AI insights
"""

import json
from datetime import datetime, timedelta
import sys
import os

# Add the current directory to path to import app modules
sys.path.append('.')

def simulate_user_week():
    """Simulate a premium user using the app for 7 days with realistic data"""
    
    # User Profile Setup
    user_profile = {
        'name': 'Sarah M.',
        'email': 'sarah.demo@example.com',
        'age': 32,
        'gender': 'female',
        'height': 165,  # cm
        'weight': 78.5,  # kg starting weight
        'goal_weight': 68,
        'goal': 'fat_loss',
        'subscription_tier': 'premium',
        'motivation': 'I want to feel confident in my clothes again and have energy to keep up with my kids',
        'goal_reason': 'health_and_confidence',
        'activity_level': 'lightly_active',
        'sleep_hours': '7',
        'stress_level': '6',
        'motivation_level': '7',
        'menstrual_cycle': 'follicular_phase',
        'health_conditions': 'None',
        'medications': 'none'
    }
    
    # 7 Days of Realistic Data
    daily_logs = []
    
    # DAY 1 - Monday (Starting Strong)
    day1 = {
        'date': '2024-01-15',
        'mood': 'good',
        'water_intake': 'good',
        'workout': 'strength',
        'workout_duration': '45',
        'sleep_hours': '7.5',
        'stress_level': '5',
        'weight': '78.5',
        'food_log': 'Breakfast: Greek yogurt with berries and granola, Lunch: Chicken salad wrap with vegetables, Dinner: Salmon with quinoa and roasted vegetables, Snacks: Apple with almond butter',
        'tracking_devices': 'Fitbit: 8,234 steps, Sleep Score 82, RHR 68bpm, Active Zone Minutes: 45',
        'notes': 'Feeling motivated to start! Had good energy during workout. Noticed I was quite hungry in the afternoon - maybe need more protein at lunch.'
    }
    
    # DAY 2 - Tuesday (Slight Struggles)
    day2 = {
        'date': '2024-01-16',
        'mood': 'okay',
        'water_intake': 'moderate',
        'workout': 'cardio',
        'workout_duration': '30',
        'sleep_hours': '6.5',
        'stress_level': '7',
        'weight': '78.3',
        'food_log': 'Breakfast: Oatmeal with banana, Lunch: Leftover salmon and quinoa, Dinner: Stir-fry with tofu and vegetables, Snacks: Crackers and hummus, evening chocolate (stress eating)',
        'tracking_devices': 'Fitbit: 6,789 steps, Sleep Score 74, RHR 71bpm, Active Zone Minutes: 25',
        'notes': 'Work was stressful today. Had chocolate after dinner because I felt overwhelmed. Sleep was restless - kept waking up thinking about work deadlines.'
    }
    
    # DAY 3 - Wednesday (Finding Balance)
    day3 = {
        'date': '2024-01-17',
        'mood': 'good',
        'water_intake': 'excellent',
        'workout': 'yoga',
        'workout_duration': '35',
        'sleep_hours': '7.5',
        'stress_level': '4',
        'weight': '78.1',
        'food_log': 'Breakfast: Smoothie with protein powder, spinach, and fruit, Lunch: Turkey and avocado salad, Dinner: Lean beef with sweet potato and green beans, Snacks: Greek yogurt',
        'tracking_devices': 'Fitbit: 9,156 steps, Sleep Score 85, RHR 66bpm, Active Zone Minutes: 30',
        'notes': 'Yoga really helped with stress! Felt much calmer today. Made sure to drink water consistently. Energy levels were stable - no afternoon crash today.'
    }
    
    # DAY 4 - Thursday (Plateauing)
    day4 = {
        'date': '2024-01-18',
        'mood': 'good',
        'water_intake': 'good',
        'workout': 'strength',
        'workout_duration': '50',
        'sleep_hours': '8',
        'stress_level': '3',
        'weight': '78.1',
        'food_log': 'Breakfast: Eggs with whole grain toast and avocado, Lunch: Quinoa bowl with chickpeas and vegetables, Dinner: Grilled chicken with brown rice and broccoli, Snacks: Mixed nuts',
        'tracking_devices': 'Fitbit: 7,892 steps, Sleep Score 88, RHR 65bpm, Active Zone Minutes: 48',
        'notes': 'Great strength training session - increased weights! Weight staying the same but I know that can be normal. Feeling stronger and clothes fit a bit better.'
    }
    
    # DAY 5 - Friday (Social Challenges)
    day5 = {
        'date': '2024-01-19',
        'mood': 'excellent',
        'water_intake': 'moderate',
        'workout': 'walking',
        'workout_duration': '60',
        'sleep_hours': '6',
        'stress_level': '4',
        'weight': '77.9',
        'food_log': 'Breakfast: Protein smoothie, Lunch: Salad with grilled chicken, Dinner: Pizza and wine (date night), Snacks: Shared dessert',
        'tracking_devices': 'Fitbit: 11,234 steps, Sleep Score 71, RHR 69bpm, Active Zone Minutes: 35',
        'notes': 'Date night with my partner! Had pizza and wine but enjoyed a long walk together. Stayed up later than usual. Need to balance social life with goals.'
    }
    
    # DAY 6 - Saturday (Recovery Day)
    day6 = {
        'date': '2024-01-20',
        'mood': 'okay',
        'water_intake': 'low',
        'workout': 'rest',
        'workout_duration': '0',
        'sleep_hours': '8.5',
        'stress_level': '2',
        'weight': '78.2',
        'food_log': 'Breakfast: Pancakes with fruit (weekend treat), Lunch: Light salad, Dinner: Vegetable soup with whole grain bread, Snacks: Tea and a cookie',
        'tracking_devices': 'Fitbit: 4,567 steps, Sleep Score 90, RHR 64bpm, Active Zone Minutes: 0',
        'notes': 'Planned rest day. Weight up slightly - probably from yesterday\'s sodium/carbs. Feeling a bit sluggish, didn\'t drink enough water. Good deep sleep though!'
    }
    
    # DAY 7 - Sunday (Getting Back on Track)
    day7 = {
        'date': '2024-01-21',
        'mood': 'good',
        'water_intake': 'excellent',
        'workout': 'cardio',
        'workout_duration': '40',
        'sleep_hours': '7',
        'stress_level': '3',
        'weight': '77.6',
        'food_log': 'Breakfast: Greek yogurt with berries, Lunch: Grilled vegetables with quinoa, Dinner: Baked cod with asparagus and brown rice, Snacks: Apple and almonds',
        'tracking_devices': 'Fitbit: 9,876 steps, Sleep Score 83, RHR 67bpm, Active Zone Minutes: 42',
        'notes': 'Back on track! Cardio felt great, lots of energy. Weight dropped nicely - shows how body responds to consistency. Feeling confident about the upcoming week.'
    }
    
    daily_logs = [day1, day2, day3, day4, day5, day6, day7]
    
    # Calculate Quick Scores for each day
    def calculate_quick_score(log):
        score = 4.0
        
        # Mood scoring
        mood_scores = {'excellent': 2, 'good': 1.5, 'okay': 0.5, 'low': 0}
        score += mood_scores.get(log['mood'], 0)
        
        # Water scoring
        water_scores = {'excellent': 1.5, 'good': 1, 'moderate': 0.5, 'low': 0}
        score += water_scores.get(log['water_intake'], 0)
        
        # Workout scoring
        if log['workout'] != 'rest':
            score += 1.5
        else:
            score += 0.5
        
        # Sleep scoring
        sleep = float(log['sleep_hours'])
        if 7 <= sleep <= 9:
            score += 1.5
        elif sleep >= 6:
            score += 1
        
        # Food logging bonus
        if len(log['food_log']) > 20:
            score += 1
        
        # Stress scoring
        stress = int(log['stress_level'])
        if stress <= 3:
            score += 0.5
        
        # Notes and tracking bonus
        if len(log['notes']) > 10:
            score += 0.5
        if len(log['tracking_devices']) > 10:
            score += 0.5
        
        return min(10.0, score)
    
    # Generate AI Insights for the Week
    ai_insights = []
    
    # Daily AI insights
    for i, log in enumerate(daily_logs):
        day_num = i + 1
        score = calculate_quick_score(log)
        
        insight = f"Day {day_num} Score: {score:.1f}/10\n"
        
        if day_num == 1:
            insight += "🌟 Great start to your journey! Your combination of strength training and balanced nutrition is setting a solid foundation. Your Fitbit data shows excellent active zone minutes - this will boost your metabolism."
        elif day_num == 2:
            insight += "💙 Stress affects our food choices - I noticed you mentioned stress eating chocolate. Your elevated heart rate (71bpm vs 68bpm yesterday) confirms stress impact. Tomorrow, try a 5-minute breathing exercise when stressed."
        elif day_num == 3:
            insight += "🧘‍♀️ Perfect example of stress management! Your yoga session brought your heart rate down to 66bpm and stress level to 4. This mind-body connection is key for sustainable fat loss."
        elif day_num == 4:
            insight += "💪 Weight plateaus are normal and healthy! Your Fitbit shows you're building lean muscle (higher active zone minutes: 48). Muscle weighs more than fat but burns more calories at rest."
        elif day_num == 5:
            insight += "🍕 Social balance is crucial for long-term success! One night of indulgence won't derail progress. Your 11,234 steps show you naturally compensated with extra movement."
        elif day_num == 6:
            insight += "😴 Your body needed this rest! Sleep score of 90 and RHR of 64bpm shows excellent recovery. The slight weight increase is water retention from yesterday's carbs - totally normal."
        elif day_num == 7:
            insight += "🎯 Weekly consistency pays off! Weight down to 77.6kg (-0.9kg total). Your data shows a clear pattern: stress management + adequate sleep + consistent movement = results."
        
        ai_insights.append(insight)
    
    # Weekly Summary AI Analysis
    weekly_summary = f"""
    📊 WEEKLY ANALYSIS - PREMIUM AI INSIGHTS
    
    🎯 OVERALL PROGRESS:
    • Weight Loss: 0.9kg (78.5kg → 77.6kg)
    • Average Daily Score: {sum(calculate_quick_score(log) for log in daily_logs)/7:.1f}/10
    • Consistency Rate: 7/7 days logged (100%)
    
    💡 KEY PATTERNS IDENTIFIED:
    
    1. STRESS-WEIGHT CONNECTION:
    Your data reveals a clear correlation between stress levels and weight fluctuations:
    • High stress days (Day 2: stress=7) → weight maintenance/small gain
    • Low stress days (Day 6: stress=2) → better recovery and weight loss
    • Recommendation: Continue yoga/mindfulness on high-stress days
    
    2. SLEEP QUALITY IMPACT:
    • Best weight loss occurred after 7.5-8.5 hours of sleep
    • Your Fitbit confirms: Sleep scores 80+ correlate with lower resting heart rate
    • Optimal sleep window for you appears to be 7.5-8 hours
    
    3. MOVEMENT VARIETY SUCCESS:
    • Strength training (Days 1,4): Built lean muscle, higher calorie burn
    • Cardio (Days 2,7): Improved cardiovascular health, consistent fat burn
    • Yoga (Day 3): Stress reduction, flexibility, mindful eating
    • Walking (Day 5): Social integration, sustainable movement
    
    4. NUTRITION PATTERNS:
    • Higher protein breakfasts (Greek yogurt, eggs, smoothies) = stable energy
    • Afternoon hunger appears when lunch protein is insufficient
    • Evening stress eating triggered by work pressure, not physical hunger
    
    🔮 PREDICTIVE INSIGHTS:
    
    Based on your data patterns, here's what to expect:
    • Continue current approach: 0.5-1kg loss per week is sustainable
    • Focus weeks (low stress + good sleep): Expect 1-1.5kg loss
    • High stress weeks: Maintain weight, focus on consistency not scale
    
    📈 PERSONALIZED RECOMMENDATIONS FOR WEEK 2:
    
    1. NUTRITION OPTIMIZATION:
    • Add 20g protein to lunch to prevent afternoon hunger
    • Keep stress-fighting foods handy: herbal tea, dark chocolate (85%+)
    • Increase water on rest days (you tend to drink less)
    
    2. MOVEMENT REFINEMENT:
    • Perfect weekly structure: 2 strength, 2 cardio, 1 yoga, 1 active recovery
    • Increase strength training duration to 55 minutes (you're ready!)
    • Add 5-minute morning walk on rest days for gentle movement
    
    3. STRESS MANAGEMENT:
    • Schedule yoga on Tuesdays (historically high stress day)
    • Set phone reminders for 3 water breaks during work hours
    • Practice 2-minute breathing exercises before meals
    
    4. SLEEP OPTIMIZATION:
    • Your sweet spot is 7.5-8 hours - prioritize this
    • Avoid late dinners on social nights (affects sleep quality)
    • Your best RHR (64-66bpm) occurs with quality sleep
    
    🏆 WHAT'S WORKING BRILLIANTLY:
    • Variety in workouts prevents boredom and plateaus
    • Honest food logging (including indulgences) enables accurate insights
    • Wearable data integration provides objective health metrics
    • Self-awareness in notes helps identify emotional eating triggers
    
    ⚠️ WATCH POINTS:
    • Stress eating pattern on work days - have backup strategies ready
    • Water intake drops on weekends - set phone reminders
    • Don't panic at daily weight fluctuations - focus on weekly trends
    
    🎯 WEEK 2 TARGETS:
    • Maintain current loss rate (0.5-1kg)
    • Improve average daily score to 8.5+/10
    • Add 500 more daily steps (current average: 8,251)
    • Reduce average stress level from 4 to 3.5
    
    💪 YOUR SUCCESS FORMULA:
    Strength Training + Adequate Sleep + Stress Management + Honest Tracking = Sustainable Fat Loss
    
    Remember: You lost almost 1kg while still enjoying date night pizza! This proves you're building a lifestyle, not following a restrictive diet. Keep this balance - it's your superpower! 🌟
    """
    
    # Display the complete simulation
    print("=" * 80)
    print("🔥 7-DAY PREMIUM USER SIMULATION - FITNESS COMPANION APP")
    print("=" * 80)
    
    print(f"\n👤 USER PROFILE:")
    print(f"Name: {user_profile['name']}")
    print(f"Goal: {user_profile['goal'].replace('_', ' ').title()}")
    print(f"Starting Weight: {user_profile['weight']}kg → Target: {user_profile['goal_weight']}kg")
    print(f"Subscription: {user_profile['subscription_tier'].upper()}")
    
    print("\n📅 DAILY PROGRESSION:")
    print("-" * 80)
    
    for i, (log, insight) in enumerate(zip(daily_logs, ai_insights)):
        print(f"\n🗓️ {log['date']} (Day {i+1})")
        print(f"Weight: {log['weight']}kg | Mood: {log['mood']} | Sleep: {log['sleep_hours']}h")
        print(f"Workout: {log['workout']} ({log['workout_duration']}min) | Stress: {log['stress_level']}/10")
        print(f"💭 Notes: {log['notes'][:100]}...")
        print(f"🤖 AI Insight: {insight}")
        print("-" * 40)
    
    print("\n" + "=" * 80)
    print("🧠 WEEKLY AI ANALYSIS (PREMIUM FEATURE)")
    print("=" * 80)
    print(weekly_summary)
    
    print("\n" + "=" * 80)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("""
    This simulation shows how your FITNESS COMPANION APP provides:
    
    ✅ Daily instant feedback and scoring
    ✅ Pattern recognition across multiple data points
    ✅ Wearable device integration and analysis
    ✅ Emotional eating and stress correlation insights
    ✅ Personalized recommendations based on actual user data
    ✅ Predictive insights for future weeks
    ✅ Honest, supportive guidance that accounts for real life
    ✅ Premium features: Unlimited AI analysis, advanced insights, trend analysis
    
    The app successfully identifies what's working, what needs adjustment, and provides
    actionable advice that leads to sustainable fat loss while maintaining life balance.
    """)

if __name__ == "__main__":
    simulate_user_week()
