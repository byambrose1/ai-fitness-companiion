"""
Enhanced Personalization Module
Connects questionnaire responses to dashboard experience for better user engagement
"""

from datetime import datetime, timedelta
import statistics
from collections import defaultdict

def generate_personalized_dashboard_content(user_profile, recent_logs, user_stats):
    """
    Generate highly personalized dashboard content based on questionnaire responses
    """
    profile_data = user_profile.get('profile_data', {})
    
    # Extract questionnaire responses
    goal = profile_data.get('goal', 'fat_loss')
    activity_level = profile_data.get('activity_level', 'moderately_active')
    dietary_preferences = profile_data.get('dietary_preferences', 'none')
    health_conditions = profile_data.get('health_conditions', 'none')
    motivation = profile_data.get('motivation', '')
    
    # Generate personalized content
    personalized_content = {
        'welcome_message': generate_personalized_welcome(user_profile, user_stats),
        'goal_progress': generate_goal_progress_message(profile_data, recent_logs, user_stats),
        'personalized_insights': generate_enhanced_insights(profile_data, recent_logs),
        'custom_recommendations': generate_custom_recommendations(profile_data, recent_logs),
        'motivation_reminder': generate_motivation_reminder(profile_data, user_stats),
        'next_steps': generate_personalized_next_steps(profile_data, recent_logs),
        'dashboard_customization': get_dashboard_customization(profile_data)
    }
    
    return personalized_content

def generate_personalized_welcome(user_profile, user_stats):
    """Generate a welcome message that references the user's specific goals"""
    profile_data = user_profile.get('profile_data', {})
    name = user_profile.get('name', '').split()[0] if user_profile.get('name') else 'there'
    
    goal = profile_data.get('goal', 'fat_loss')
    activity_level = profile_data.get('activity_level', '')
    streak = user_stats.get('streak_days', 0)
    
    # Goal-specific welcome messages
    goal_messages = {
        'fat_loss': f"Welcome back, {name}! Ready to continue your fat loss journey?",
        'muscle_gain': f"Hey {name}! Time to build some muscle today!",
        'endurance': f"Welcome back, {name}! Let's boost that endurance!",
        'strength': f"Hello {name}! Ready to get stronger today?",
        'general_fitness': f"Hi {name}! Let's keep building those healthy habits!"
    }
    
    base_message = goal_messages.get(goal, goal_messages['fat_loss'])
    
    # Add streak motivation
    if streak > 0:
        if streak >= 7:
            base_message += f" 🔥 Amazing {streak}-day streak!"
        elif streak >= 3:
            base_message += f" 💪 {streak} days strong!"
        else:
            base_message += f" 🌟 Day {streak} - building momentum!"
    
    # Add activity level context
    activity_context = {
        'sedentary': "Every small step counts!",
        'lightly_active': "Your consistent activity is paying off!",
        'moderately_active': "Love your balanced approach to fitness!",
        'very_active': "Your dedication to staying active is inspiring!",
        'extremely_active': "Your high activity level is incredible!"
    }
    
    if activity_level in activity_context:
        base_message += f" {activity_context[activity_level]}"
    
    return base_message

def generate_goal_progress_message(profile_data, recent_logs, user_stats):
    """Generate progress message specific to user's stated goals"""
    goal = profile_data.get('goal', 'fat_loss')
    total_logs = user_stats.get('total_logs', 0)
    
    if total_logs == 0:
        goal_starters = {
            'fat_loss': "Ready to start your fat loss journey? Your first log will help us understand your patterns and create a personalized plan!",
            'muscle_gain': "Let's begin building muscle! Track your workouts and protein intake to see amazing results.",
            'endurance': "Time to build that cardiovascular fitness! Start logging your cardio activities and watch your stamina improve.",
            'strength': "Ready to get stronger? Track your strength training sessions and progressive overload.",
            'general_fitness': "Let's build healthy habits together! Start with small, consistent actions."
        }
        return goal_starters.get(goal, goal_starters['fat_loss'])
    
    # Analyze progress based on goal
    if goal == 'fat_loss':
        return analyze_fat_loss_progress(recent_logs, user_stats)
    elif goal == 'muscle_gain':
        return analyze_muscle_gain_progress(recent_logs, user_stats)
    elif goal == 'endurance':
        return analyze_endurance_progress(recent_logs, user_stats)
    elif goal == 'strength':
        return analyze_strength_progress(recent_logs, user_stats)
    else:
        return analyze_general_fitness_progress(recent_logs, user_stats)

def analyze_fat_loss_progress(recent_logs, user_stats):
    """Analyze progress specifically for fat loss goals"""
    if not recent_logs:
        return "Start logging to track your fat loss progress! Focus on creating a sustainable calorie deficit."
    
    # Check weight trend
    weights = [float(log.get('weight', 0)) for log in recent_logs if log.get('weight')]
    if len(weights) >= 2:
        weight_change = weights[-1] - weights[0]
        if weight_change <= -1:
            return f"Excellent! You're down {abs(weight_change):.1f}lbs - your fat loss plan is working! 🎉"
        elif weight_change <= 0:
            return "Great job maintaining! Small fluctuations are normal - focus on the trend over time."
        else:
            return "Weight can fluctuate daily. Focus on your habits - the results will follow! 💪"
    
    # Check consistency
    streak = user_stats.get('streak_days', 0)
    if streak >= 7:
        return "Your consistency is the key to fat loss success! Keep up this amazing routine."
    else:
        return "Building consistent habits is crucial for fat loss. You're on the right track!"

def analyze_muscle_gain_progress(recent_logs, user_stats):
    """Analyze progress for muscle gain goals"""
    if not recent_logs:
        return "Ready to build muscle? Focus on progressive overload and adequate protein intake!"
    
    # Check workout consistency
    workouts = [log for log in recent_logs if log.get('workout_duration', 0) > 0]
    strength_workouts = [log for log in recent_logs if 'strength' in log.get('workout', '').lower() or 'weight' in log.get('workout', '').lower()]
    
    if len(strength_workouts) >= 3:
        return "Fantastic strength training consistency! Muscle growth happens with progressive overload and recovery. 💪"
    elif len(workouts) >= 3:
        return "Good workout consistency! Try adding more strength training for optimal muscle gain."
    else:
        return "Muscle gain requires consistent strength training. Aim for 3-4 sessions per week!"

def analyze_endurance_progress(recent_logs, user_stats):
    """Analyze progress for endurance goals"""
    if not recent_logs:
        return "Let's build your cardiovascular endurance! Start with activities you enjoy."
    
    cardio_workouts = [log for log in recent_logs if any(word in log.get('workout', '').lower() for word in ['cardio', 'running', 'cycling', 'swimming', 'walking'])]
    
    if len(cardio_workouts) >= 4:
        return "Outstanding cardio consistency! Your endurance is definitely improving with this routine. 🏃‍♀️"
    elif len(cardio_workouts) >= 2:
        return "Good cardio frequency! Try to add one more session this week for faster endurance gains."
    else:
        return "Endurance improves with regular cardio. Aim for 3-4 cardio sessions per week!"

def analyze_strength_progress(recent_logs, user_stats):
    """Analyze progress for strength goals"""
    if not recent_logs:
        return "Ready to get stronger? Focus on compound movements and progressive overload!"
    
    strength_indicators = [log for log in recent_logs if any(word in log.get('workout', '').lower() for word in ['strength', 'weights', 'lifting', 'deadlift', 'squat', 'bench'])]
    
    if len(strength_indicators) >= 3:
        return "Excellent strength training frequency! Progressive overload is key to getting stronger. 💪"
    else:
        return "Strength gains come from consistent resistance training. Aim for 3-4 strength sessions weekly!"

def analyze_general_fitness_progress(recent_logs, user_stats):
    """Analyze progress for general fitness goals"""
    streak = user_stats.get('streak_days', 0)
    total_logs = user_stats.get('total_logs', 0)
    
    if streak >= 7:
        return "Amazing consistency! You're building strong healthy habits that will last a lifetime. 🌟"
    elif total_logs >= 5:
        return "Great progress building healthy habits! Consistency is more important than perfection."
    else:
        return "Every healthy choice counts! Focus on building one habit at a time."

def generate_enhanced_insights(profile_data, recent_logs):
    """Generate insights that directly reference questionnaire responses"""
    insights = []
    
    goal = profile_data.get('goal', 'fat_loss')
    activity_level = profile_data.get('activity_level', '')
    dietary_preferences = profile_data.get('dietary_preferences', '')
    health_conditions = profile_data.get('health_conditions', '')
    
    # Goal-specific insights
    if goal == 'fat_loss':
        insights.extend(get_fat_loss_insights(recent_logs, profile_data))
    elif goal == 'muscle_gain':
        insights.extend(get_muscle_gain_insights(recent_logs, profile_data))
    
    # Activity level insights
    if activity_level == 'sedentary':
        insights.append({
            'type': 'info',
            'icon': '🚶‍♀️',
            'category': 'Activity',
            'message': 'Since you mentioned being sedentary, start with 10-15 minute walks. Small steps lead to big changes!',
            'action': 'Take a 10-minute walk after your next meal.'
        })
    elif activity_level == 'very_active':
        insights.append({
            'type': 'warning',
            'icon': '😴',
            'category': 'Recovery',
            'message': 'With your high activity level, recovery is crucial. Are you getting enough rest?',
            'action': 'Schedule at least one full rest day this week.'
        })
    
    # Dietary preference insights
    if 'vegetarian' in dietary_preferences.lower():
        insights.append({
            'type': 'info',
            'icon': '🌱',
            'category': 'Nutrition',
            'message': 'As a vegetarian, focus on complete proteins like quinoa, beans, and Greek yogurt.',
            'action': 'Add a plant-based protein source to your next meal.'
        })
    elif 'vegan' in dietary_preferences.lower():
        insights.append({
            'type': 'info',
            'icon': '🥜',
            'category': 'Nutrition',
            'message': 'Vegan protein sources like lentils, nuts, and seeds will support your goals.',
            'action': 'Try a handful of nuts or seeds as your next snack.'
        })
    
    # Health condition considerations
    if 'diabetes' in health_conditions.lower():
        insights.append({
            'type': 'info',
            'icon': '🩺',
            'category': 'Health',
            'message': 'With diabetes, consistent meal timing and blood sugar monitoring are important.',
            'action': 'Log your meals at regular intervals to help manage blood sugar.'
        })
    
    return insights

def get_fat_loss_insights(recent_logs, profile_data):
    """Specific insights for fat loss goals"""
    insights = []
    
    if recent_logs:
        # Calorie deficit indicators
        high_calorie_days = len([log for log in recent_logs if 'takeaway' in log.get('food_log', '').lower() or 'pizza' in log.get('food_log', '').lower()])
        if high_calorie_days >= len(recent_logs) * 0.4:
            insights.append({
                'type': 'warning',
                'icon': '🍕',
                'category': 'Fat Loss',
                'message': 'Frequent high-calorie meals can slow fat loss. Let\'s focus on home-cooked options.',
                'action': 'Plan 3 simple, healthy meals for this week.'
            })
        
        # Water intake for fat loss
        poor_water_days = len([log for log in recent_logs if log.get('water_intake') in ['< 1L', '1-2L']])
        if poor_water_days >= len(recent_logs) * 0.5:
            insights.append({
                'type': 'info',
                'icon': '💧',
                'category': 'Fat Loss',
                'message': 'Proper hydration boosts metabolism and helps control appetite for fat loss.',
                'action': 'Drink a glass of water before each meal today.'
            })
    
    return insights

def get_muscle_gain_insights(recent_logs, profile_data):
    """Specific insights for muscle gain goals"""
    insights = []
    
    if recent_logs:
        # Protein tracking
        protein_mentions = len([log for log in recent_logs if any(word in log.get('food_log', '').lower() for word in ['protein', 'chicken', 'fish', 'eggs', 'yogurt'])])
        if protein_mentions < len(recent_logs) * 0.6:
            insights.append({
                'type': 'warning',
                'icon': '🥩',
                'category': 'Muscle Gain',
                'message': 'Adequate protein is essential for muscle growth. Aim for protein at every meal.',
                'action': 'Add a protein source to your next meal or snack.'
            })
        
        # Recovery for muscle gain
        poor_sleep_days = len([log for log in recent_logs if float(log.get('sleep_hours', 8)) < 7])
        if poor_sleep_days >= len(recent_logs) * 0.4:
            insights.append({
                'type': 'warning',
                'icon': '😴',
                'category': 'Muscle Gain',
                'message': 'Muscle growth happens during sleep. Poor sleep can limit your gains.',
                'action': 'Aim for 7-9 hours of sleep tonight for optimal recovery.'
            })
    
    return insights

def generate_custom_recommendations(profile_data, recent_logs):
    """Generate recommendations based on specific user profile"""
    recommendations = []
    
    goal = profile_data.get('goal', 'fat_loss')
    activity_level = profile_data.get('activity_level', '')
    
    # Goal-specific recommendations
    goal_recommendations = {
        'fat_loss': [
            "Create a moderate calorie deficit through portion control",
            "Focus on whole foods and home cooking",
            "Include both cardio and strength training",
            "Stay hydrated to support metabolism"
        ],
        'muscle_gain': [
            "Prioritize progressive overload in strength training",
            "Eat adequate protein (1.6-2.2g per kg body weight)",
            "Allow proper recovery between workouts",
            "Consider a slight calorie surplus"
        ],
        'endurance': [
            "Gradually increase cardio duration and intensity",
            "Include both steady-state and interval training",
            "Focus on proper fueling before/after workouts",
            "Build a strong aerobic base"
        ]
    }
    
    recommendations.extend(goal_recommendations.get(goal, goal_recommendations['fat_loss']))
    
    return recommendations

def generate_motivation_reminder(profile_data, user_stats):
    """Generate motivation based on user's original goals"""
    motivation = profile_data.get('motivation', '')
    goal = profile_data.get('goal', 'fat_loss')
    streak = user_stats.get('streak_days', 0)
    
    if motivation:
        return f"Remember why you started: \"{motivation}\" - you're {streak} days closer to that goal!"
    
    # Default motivational messages by goal
    default_motivation = {
        'fat_loss': f"You're {streak} days into building sustainable fat loss habits!",
        'muscle_gain': f"Every workout is building the stronger you - {streak} days of progress!",
        'endurance': f"Your endurance is improving with each session - {streak} days of consistency!",
        'strength': f"You're getting stronger every day - {streak} days of dedication!",
        'general_fitness': f"Building healthy habits one day at a time - {streak} days strong!"
    }
    
    return default_motivation.get(goal, default_motivation['fat_loss'])

def generate_personalized_next_steps(profile_data, recent_logs):
    """Generate next steps based on user's specific situation"""
    goal = profile_data.get('goal', 'fat_loss')
    activity_level = profile_data.get('activity_level', '')
    
    if not recent_logs:
        return get_beginner_next_steps(goal, activity_level)
    
    return get_progressive_next_steps(goal, recent_logs)

def get_beginner_next_steps(goal, activity_level):
    """Next steps for users just starting"""
    steps = {
        'fat_loss': [
            "Complete your first daily log to establish baseline",
            "Focus on logging food honestly for 3 days",
            "Add 10 minutes of walking daily",
            "Drink water before each meal"
        ],
        'muscle_gain': [
            "Start with 2-3 strength training sessions per week",
            "Track protein intake at each meal",
            "Focus on compound movements",
            "Ensure adequate rest between sessions"
        ]
    }
    
    return steps.get(goal, steps['fat_loss'])

def get_progressive_next_steps(goal, recent_logs):
    """Next steps for users with some data"""
    # Analyze recent patterns and suggest improvements
    steps = []
    
    # Check consistency
    if len(recent_logs) < 5:
        steps.append("Focus on daily logging consistency")
    
    # Check workout frequency
    workout_days = len([log for log in recent_logs if log.get('workout_duration', 0) > 0])
    if workout_days < 3:
        steps.append("Increase workout frequency to 3-4 times per week")
    
    # Check sleep
    poor_sleep_days = len([log for log in recent_logs if float(log.get('sleep_hours', 8)) < 7])
    if poor_sleep_days >= len(recent_logs) * 0.4:
        steps.append("Prioritize 7-9 hours of sleep nightly")
    
    return steps if steps else ["Keep up your excellent consistency!"]

def get_dashboard_customization(profile_data):
    """Get dashboard customization based on user preferences"""
    goal = profile_data.get('goal', 'fat_loss')
    
    customization = {
        'primary_metrics': [],
        'color_scheme': '',
        'focus_areas': [],
        'chart_priorities': []
    }
    
    if goal == 'fat_loss':
        customization.update({
            'primary_metrics': ['weight', 'water_intake', 'sleep_hours'],
            'color_scheme': 'green',
            'focus_areas': ['Calorie Balance', 'Hydration', 'Sleep Quality'],
            'chart_priorities': ['weight_trend', 'daily_score', 'water_intake']
        })
    elif goal == 'muscle_gain':
        customization.update({
            'primary_metrics': ['workout_duration', 'protein_intake', 'sleep_hours'],
            'color_scheme': 'blue',
            'focus_areas': ['Strength Training', 'Protein Intake', 'Recovery'],
            'chart_priorities': ['workout_frequency', 'protein_trend', 'sleep_quality']
        })
    
    return customization
