import os
from datetime import timedelta

class Config:
    # Basic Flask config
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///reminders.db')
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    
    # Email
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_NAME = os.getenv('SENDER_NAME')
    DEFAULT_RECIPIENT_EMAIL = os.getenv('DEFAULT_RECIPIENT_EMAIL')
    
    # Redis (for task queue)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Celery
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BEAT_SCHEDULE = {
        'check-reminders': {
            'task': 'app.tasks.check_reminders',
            'schedule': timedelta(minutes=1)
        }
    } 