from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import csv
from io import StringIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
from enum import Enum

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'reminders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration from .env
app.config['SMTP_SERVER'] = os.getenv('SMTP_SERVER')
app.config['SMTP_PORT'] = int(os.getenv('SMTP_PORT'))
app.config['SMTP_USERNAME'] = os.getenv('SMTP_USERNAME')
app.config['SMTP_PASSWORD'] = os.getenv('SMTP_PASSWORD')
app.config['SENDER_EMAIL'] = os.getenv('SENDER_EMAIL')
app.config['SENDER_NAME'] = os.getenv('SENDER_NAME')
app.config['DEFAULT_RECIPIENT_EMAIL'] = os.getenv('DEFAULT_RECIPIENT_EMAIL')

db = SQLAlchemy(app)

# Add FrequencyType Enum
class FrequencyType(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

# Models
class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    frequency = db.Column(db.String(20), nullable=False, default=FrequencyType.ONCE)
    last_sent = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)  # For recurring reminders

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'description': self.description,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    default_email = db.Column(db.String(120), nullable=False)
    sender_name = db.Column(db.String(120), nullable=False)

    def to_dict(self):
        return {
            'default_email': self.default_email,
            'sender_name': self.sender_name
        }

# Create database tables
def init_db():
    with app.app_context():
        db.create_all()
        # Create default settings if they don't exist
        if not Settings.query.first():
            default_settings = Settings(
                default_email=app.config['DEFAULT_RECIPIENT_EMAIL'],
                sender_name=app.config['SENDER_NAME']
            )
            db.session.add(default_settings)
            db.session.commit()

def send_email(to_email, subject, body):
    """Send email using configured SMTP server"""
    try:
        msg = MIMEMultipart()
        sender = f"{app.config['SENDER_NAME']} <{app.config['SENDER_EMAIL']}>"
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(app.config['SMTP_SERVER'], app.config['SMTP_PORT'])
        server.starttls()
        server.login(app.config['SMTP_USERNAME'], app.config['SMTP_PASSWORD'])
        
        text = msg.as_string()
        server.sendmail(app.config['SENDER_EMAIL'], to_email, text)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def check_reminders():
    """Check for due reminders and send notifications"""
    with app.app_context():
        try:
            now = datetime.utcnow()
            
            # Get all reminders that need to be checked
            reminders = Reminder.query.filter(
                (Reminder.end_date.is_(None) | (Reminder.end_date >= now))
            ).all()

            for reminder in reminders:
                should_send = False
                
                if reminder.last_sent is None:
                    # Never sent before
                    if reminder.date <= now:
                        should_send = True
                else:
                    # Check based on frequency
                    if reminder.frequency == FrequencyType.ONCE:
                        should_send = reminder.date <= now and not reminder.last_sent
                    elif reminder.frequency == FrequencyType.DAILY:
                        should_send = (now - reminder.last_sent).days >= 1
                    elif reminder.frequency == FrequencyType.WEEKLY:
                        should_send = (now - reminder.last_sent).days >= 7
                    elif reminder.frequency == FrequencyType.MONTHLY:
                        # Check if it's been a month since last sent
                        next_date = reminder.last_sent.replace(month=reminder.last_sent.month + 1)
                        should_send = now >= next_date
                    elif reminder.frequency == FrequencyType.YEARLY:
                        # Check if it's been a year since last sent
                        next_date = reminder.last_sent.replace(year=reminder.last_sent.year + 1)
                        should_send = now >= next_date

                if should_send:
                    subject = f"Reminder: {reminder.description}"
                    body = f"""
                    Hello!

                    This is your {reminder.frequency} reminder for: {reminder.description}
                    Originally scheduled for: {reminder.date.strftime('%Y-%m-%d %H:%M')}

                    Frequency: {reminder.frequency.capitalize()}
                    {f"End Date: {reminder.end_date.strftime('%Y-%m-%d')}" if reminder.end_date else ""}

                    Best regards,
                    {app.config['SENDER_NAME']}
                    """
                    
                    if send_email(reminder.email, subject, body):
                        reminder.last_sent = now
                        db.session.commit()
                        logger.info(f"Reminder sent for ID: {reminder.id}")
                    else:
                        logger.error(f"Failed to send reminder for ID: {reminder.id}")
                    
        except Exception as e:
            logger.error(f"Error in check_reminders: {str(e)}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_reminders, trigger="interval", minutes=1)
scheduler.start()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    try:
        data = request.form
        date = datetime.strptime(data['date'], '%Y-%m-%d')
        description = data['description']
        email = data.get('email', app.config['DEFAULT_RECIPIENT_EMAIL'])
        frequency = data.get('frequency', FrequencyType.ONCE)
        end_date = None

        if 'end_date' in data and data['end_date']:
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')

        reminder = Reminder(
            date=date,
            description=description,
            email=email,
            frequency=frequency,
            end_date=end_date
        )
        db.session.add(reminder)
        db.session.commit()

        # Send confirmation email
        subject = f"Reminder Confirmation - {app.config['SENDER_NAME']}"
        body = f"""
        Hello!

        Your {frequency} reminder has been set successfully:
        Description: {description}
        Start Date: {date.strftime('%Y-%m-%d')}
        Frequency: {frequency.capitalize()}
        {f"End Date: {end_date.strftime('%Y-%m-%d')}" if end_date else ""}

        You will receive notifications according to the frequency settings.

        Best regards,
        {app.config['SENDER_NAME']}
        """
        send_email(email, subject, body)

        return jsonify({
            'status': 'success',
            'message': 'Reminder added successfully'
        })
    except Exception as e:
        logger.error(f"Error adding reminder: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/get_reminders')
def get_all_reminders():
    try:
        reminders = Reminder.query.order_by(Reminder.date).all()
        return jsonify([{
            'id': reminder.id,
            'date': reminder.date.strftime('%Y-%m-%d'),
            'description': reminder.description,
            'email': reminder.email,
            'sent': reminder.sent
        } for reminder in reminders])
    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}")
        return jsonify([])

@app.route('/test_email', methods=['POST'])
def test_email():
    try:
        email = request.form.get('email', app.config['DEFAULT_RECIPIENT_EMAIL'])
        subject = f"Test Email from {app.config['SENDER_NAME']}"
        body = f"""
        Hello!

        This is a test email from your {app.config['SENDER_NAME']}.
        If you received this email, your email notifications are working correctly.

        Best regards,
        {app.config['SENDER_NAME']}
        """
        
        if send_email(email, subject, body):
            return jsonify({
                'status': 'success',
                'message': f'Test email sent successfully to {email}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send test email'
            }), 500
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/upload_csv', methods=['POST'])
def upload_csv_file():
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400

        file = request.files['file']
        email = request.form['email']

        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400

        if not file.filename.endswith('.csv'):
            return jsonify({
                'status': 'error',
                'message': 'Please upload a CSV file'
            }), 400

        df = pd.read_csv(file)
        
        if not all(col in df.columns for col in ['date', 'description']):
            return jsonify({
                'status': 'error',
                'message': 'CSV must contain date and description columns'
            }), 400

        reminders_added = 0
        for _, row in df.iterrows():
            try:
                date = datetime.strptime(row['date'], '%Y-%m-%d')
                reminder = Reminder(
                    date=date,
                    description=row['description'],
                    email=email
                )
                db.session.add(reminder)
                reminders_added += 1
            except Exception as e:
                logger.error(f"Error processing CSV row: {str(e)}")
                continue

        db.session.commit()

        # Send confirmation email
        subject = "CSV Reminders Added"
        body = f"""
        Hello!

        {reminders_added} reminders have been successfully imported from your CSV file.
        You will receive notifications for each reminder on their scheduled dates.

        Best regards,
        Your Reminder System
        """
        send_email(email, subject, body)

        return jsonify({
            'status': 'success',
            'message': f'Successfully imported {reminders_added} reminders'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading CSV: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/health')
def health_check():
    try:
        # Test database connection
        db.session.query(Settings).first()
        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'database': 'disconnected',
            'error': str(e)
        }), 500

@app.route('/reminders', methods=['GET'])
def get_reminders():
    try:
        reminders = Reminder.query.order_by(Reminder.date).all()
        return jsonify({
            'status': 'success',
            'reminders': [reminder.to_dict() for reminder in reminders]
        })
    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch reminders',
            'error': str(e)
        }), 500

@app.route('/reminders', methods=['POST'])
def create_reminder():
    try:
        data = request.json
        if not all(key in data for key in ['date', 'description', 'email']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        reminder = Reminder(
            date=datetime.fromisoformat(data['date']),
            description=data['description'],
            email=data['email']
        )
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Reminder created successfully',
            'reminder': reminder.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    try:
        reminder = Reminder.query.get_or_404(reminder_id)
        db.session.delete(reminder)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'Reminder {reminder_id} deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/settings', methods=['GET'])
def get_settings():
    try:
        settings = Settings.query.first()
        if not settings:
            return jsonify({
                'status': 'success',
                'settings': {
                    'default_email': '',
                    'sender_name': ''
                }
            })
        return jsonify({
            'status': 'success',
            'settings': settings.to_dict()
        })
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch settings',
            'error': str(e)
        }), 500

@app.route('/settings', methods=['POST'])
def update_settings():
    try:
        data = request.json
        if not data or 'default_email' not in data or 'sender_name' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        settings = Settings.query.first()
        if not settings:
            settings = Settings()
        
        settings.default_email = data['default_email']
        settings.sender_name = data['sender_name']
        
        db.session.add(settings)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Settings updated successfully',
            'settings': settings.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update settings',
            'error': str(e)
        }), 500

@app.route('/sample_csv')
def get_sample_csv():
    sample_data = {
        'date': ['2024-03-20T10:00:00', '2024-03-21T15:30:00'],
        'description': ['Team meeting', 'Project deadline'],
        'email': ['team@example.com', 'manager@example.com']
    }
    df = pd.DataFrame(sample_data)
    df.to_csv('sample_reminder_template.csv', index=False)
    return send_file('sample_reminder_template.csv', as_attachment=True)

if __name__ == '__main__':
    # Verify email configuration
    logger.info("Starting server with email configuration:")
    logger.info(f"SMTP Server: {app.config['SMTP_SERVER']}")
    logger.info(f"SMTP Port: {app.config['SMTP_PORT']}")
    logger.info(f"Sender Email: {app.config['SENDER_EMAIL']}")
    logger.info(f"Sender Name: {app.config['SENDER_NAME']}")
    logger.info(f"Default Recipient: {app.config['DEFAULT_RECIPIENT_EMAIL']}")
    
    init_db()  # Initialize database and create tables
    app.run(debug=True, port=5001) 