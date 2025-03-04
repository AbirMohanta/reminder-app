import os
from pathlib import Path

class Config:
    # Basic Flask config
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # In production (Render), use the /data directory
    if os.getenv('RENDER'):
        DB_DIR = '/data'
    else:
        # In development, use local instance directory
        DB_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    
    # Ensure database directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Set database path
    DB_PATH = os.path.join(DB_DIR, 'reminders.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    
    # Email configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_NAME = os.getenv('SENDER_NAME', 'Reminder App')
    DEFAULT_RECIPIENT_EMAIL = os.getenv('DEFAULT_RECIPIENT_EMAIL', 'default@example.com') 