import sqlite3
import json
from datetime import datetime

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
            subscription_tier TEXT DEFAULT 'free',
            subscription_status TEXT DEFAULT 'active',
            stripe_customer_id TEXT,
            profile_data TEXT
        )
    ''')

    # Daily logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            date TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')

    # Weekly checkins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            week_of TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')

    conn.commit()
    conn.close()

def get_user(email):
    """Get user by email"""
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user_row = cursor.fetchone()

    if not user_row:
        conn.close()
        return None

    # Get daily logs
    cursor.execute('SELECT data FROM daily_logs WHERE user_email = ? ORDER BY timestamp', (email,))
    daily_logs = [json.loads(row[0]) for row in cursor.fetchall()]

    # Get weekly checkins
    cursor.execute('SELECT data FROM weekly_checkins WHERE user_email = ? ORDER BY timestamp', (email,))
    weekly_checkins = [json.loads(row[0]) for row in cursor.fetchall()]

    conn.close()

    # Reconstruct user object
    user = {
        'email': user_row[0],
        'name': user_row[1],
        'password': user_row[2],
        'created_at': user_row[3],
        'subscription_tier': user_row[4],
        'subscription_status': user_row[5],
        'stripe_customer_id': user_row[6],
        'profile_data': json.loads(user_row[7]) if user_row[7] else {},
        'daily_logs': daily_logs,
        'weekly_checkins': weekly_checkins
    }

    return user

def save_user(user_data):
    """Save or update user"""
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (email, name, password, created_at, subscription_tier, subscription_status, stripe_customer_id, profile_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_data['email'],
        user_data['name'],
        user_data['password'],
        user_data['created_at'],
        user_data.get('subscription_tier', 'free'),
        user_data.get('subscription_status', 'active'),
        user_data.get('stripe_customer_id'),
        json.dumps(user_data.get('profile_data', {}))
    ))

    conn.commit()
    conn.close()

def add_daily_log(email, log_data):
    """Add daily log for user"""
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO daily_logs (user_email, date, timestamp, data)
        VALUES (?, ?, ?, ?)
    ''', (email, log_data['date'], log_data['timestamp'], json.dumps(log_data)))

    conn.commit()
    conn.close()

def get_user_logs(email):
    """Get daily logs for a specific user"""
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()

    cursor.execute('SELECT data FROM daily_logs WHERE user_email = ? ORDER BY timestamp DESC', (email,))
    logs = [json.loads(row[0]) for row in cursor.fetchall()]

    conn.close()
    return logs

def get_user_checkins(email):
    """Get weekly checkins for a specific user"""
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()

    cursor.execute('SELECT data FROM weekly_checkins WHERE user_email = ? ORDER BY timestamp DESC', (email,))
    checkins = [json.loads(row[0]) for row in cursor.fetchall()]

    conn.close()
    return checkins

def add_weekly_checkin(email, checkin_data):
    """Add weekly checkin for user"""
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO weekly_checkins (user_email, week_of, timestamp, data)
        VALUES (?, ?, ?, ?)
    ''', (email, checkin_data['week_of'], checkin_data['timestamp'], json.dumps(checkin_data)))

    conn.commit()
    conn.close()

def get_all_users():
    """Get all users for admin interface"""
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()

    cursor.execute('SELECT email, name, subscription_tier FROM users')
    users = cursor.fetchall()

    conn.close()
    return users

# Initialize database when module is imported
init_database()