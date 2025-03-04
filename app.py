from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import csv
from io import StringIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from dotenv import load_dotenv
from enum import Enum
import re
import io
from dateutil import parser
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask extensions
db = SQLAlchemy()

# Models
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    default_email = db.Column(db.String(120), nullable=False)
    sender_name = db.Column(db.String(120), nullable=False)

    def to_dict(self):
        return {
            'default_email': self.default_email,
            'sender_name': self.sender_name
        }

def init_db(app):
    """Initialize database and create tables"""
    try:
        # Log database configuration
        logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        logger.info(f"Database directory: {os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))}")
        
        # Ensure the database directory exists
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not db_path:
            raise ValueError("Invalid database URI")
            
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            logger.info(f"Creating database directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
        
        with app.app_context():
            # Create tables if they don't exist
            db.create_all()
            logger.info(f"Database tables created successfully at {db_path}")
            
            # Create default settings if they don't exist
            if not Settings.query.first():
                default_settings = Settings(
                    default_email=app.config.get('DEFAULT_RECIPIENT_EMAIL'),
                    sender_name=app.config.get('SENDER_NAME')
                )
                db.session.add(default_settings)
                db.session.commit()
                logger.info("Created default settings")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        logger.error(f"Current working directory: {os.getcwd()}")
        logger.error(f"Directory contents: {os.listdir('.')}")
        raise e

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    
    # Configure logging for the app
    if not app.debug:
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Reminder App startup')
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    
    # Apply proxy fix for proper IP handling
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize database
    init_db(app)
    
    return app

app = create_app()

# Add FrequencyType Enum
class FrequencyType(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

# Models
class Reminder(db.Model):
    """Model for storing reminders"""
    __tablename__ = 'reminder'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    frequency = db.Column(db.String(50), default='once')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_sent = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Reminder {self.description[:20]}...>'

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%d-%m-%Y'),
            'description': self.description,
            'email': self.email,
            'created_at': self.created_at.strftime('%d-%m-%Y %H:%M'),
            'frequency': self.frequency,
            'end_date': self.end_date.strftime('%d-%m-%Y') if self.end_date else None
        }

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
                    Originally scheduled for: {reminder.date.strftime('%d-%m-%Y %H:%M')}

                    Frequency: {reminder.frequency.capitalize()}
                    {f"End Date: {reminder.end_date.strftime('%d-%m-%Y')}" if reminder.end_date else ""}

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

def format_date_for_display(date_obj):
    """Convert datetime to display format (DD-MM-YYYY)"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%d-%m-%Y')
    return None

def parse_date_string(date_string):
    """Parse any date string to datetime object"""
    try:
        # First try explicit formats
        formats = ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # If that fails, try dateutil parser
        return parser.parse(date_string)
    except:
        return None

@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    try:
        data = request.get_json()
        
        # Convert string date to datetime object
        reminder_date = parse_date_string(data.get('date'))
        if not reminder_date:
            return jsonify({"error": "Invalid date format. Use DD-MM-YYYY"}), 400

        new_reminder = Reminder(
            date=reminder_date,
            description=data.get('description', '').strip(),
            email=data.get('email', '').strip(),
            frequency=data.get('frequency', 'once'),
            created_at=datetime.now()
        )

        db.session.add(new_reminder)
        db.session.commit()

        return jsonify({"message": "Reminder added successfully"}), 200

    except Exception as e:
        print(f"Error adding reminder: {str(e)}")  # Debug log
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/get_reminders', methods=['GET'])
def get_reminders():
    try:
        reminders = Reminder.query.all()
        return jsonify([{
            'id': r.id,
            'date': r.date.strftime('%Y-%m-%d'),
            'description': r.description,
            'email': r.email,
            'frequency': r.frequency
        } for r in reminders])
    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}")
        return jsonify({'error': 'Failed to fetch reminders'}), 500

@app.route('/test_email', methods=['POST'])
def test_email():
    try:
        data = request.get_json()
        email = data.get('email')
        if not email:
            return jsonify({"error": "Email is required"}), 400

        subject = "Test Email from Reminder App"
        body = "This is a test email from your Reminder App."
        
        send_email(email, subject, body)
        return jsonify({"message": "Test email sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a CSV"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"))
        csv_reader = csv.DictReader(stream)
        
        success_count = 0
        errors = []

        for row in csv_reader:
            try:
                reminder_date = parse_date_string(row.get('date'))
                if not reminder_date:
                    errors.append(f"Invalid date format in row: {row.get('date')}")
                    continue

                reminder = Reminder(
                    date=reminder_date,
                    description=row.get('description', '').strip(),
                    email=row.get('email', '').strip(),
                    frequency=row.get('frequency', 'once').strip().lower(),
                    created_at=datetime.now()
                )
                
                db.session.add(reminder)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Error in row: {str(e)}")
                continue

        db.session.commit()
        
        return jsonify({
            "message": f"Successfully added {success_count} reminders",
            "errors": errors if errors else None
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to process CSV: {str(e)}"}), 500

@app.route('/health')
def health_check():
    """Health check endpoint to verify application status"""
    try:
        # Test database connection
        db.session.query(Settings).first()
        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'timestamp': datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'database': 'disconnected',
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

@app.route('/delete_reminder/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    try:
        reminder = Reminder.query.get_or_404(reminder_id)
        db.session.delete(reminder)
        db.session.commit()
        return jsonify({"message": "Reminder deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/edit_reminder/<int:reminder_id>', methods=['PUT'])
def edit_reminder(reminder_id):
    try:
        data = request.get_json()
        reminder = Reminder.query.get(reminder_id)
        
        if not reminder:
            return jsonify({"error": "Reminder not found"}), 404

        # Parse and validate the date
        try:
            date_str = data.get('date')
            reminder.date = parse_date_string(date_str)
        except:
            return jsonify({"error": "Invalid date format"}), 400

        # Update other fields
        reminder.description = data.get('description', reminder.description)
        reminder.email = data.get('email', reminder.email)
        reminder.frequency = data.get('frequency', reminder.frequency)

        db.session.commit()
        return jsonify({"message": "Reminder updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['date', 'description', 'email', 'frequency'])
        
        # Write sample row
        writer.writerow(['25-03-2024', 'Sample Reminder', 'example@email.com', 'once'])
        
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=sample_reminder.csv'
        }
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset_database', methods=['POST'])
def reset_database():
    try:
        # Simple reset - just delete all reminders
        db.session.query(Reminder).delete()
        db.session.commit()
        return jsonify({"message": "Database reset successful"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def standardize_date(date_input):
    """Convert any date format to datetime object"""
    if isinstance(date_input, datetime):
        return date_input
    
    if isinstance(date_input, str):
        # Try common date formats
        formats = [
            '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d',
            '%d-%m-%y', '%y-%m-%d', '%d/%m/%y', '%y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_input, fmt)
            except ValueError:
                continue
            
        # Try parsing with dateutil as fallback
        try:
            from dateutil import parser
            return parser.parse(date_input)
        except:
            raise ValueError(f"Could not parse date: {date_input}")
    
    raise ValueError("Invalid date input")

if __name__ == '__main__':
    # Verify email configuration
    logger.info("Starting server with email configuration:")
    logger.info(f"SMTP Server: {app.config['SMTP_SERVER']}")
    logger.info(f"SMTP Port: {app.config['SMTP_PORT']}")
    logger.info(f"Sender Email: {app.config['SENDER_EMAIL']}")
    logger.info(f"Sender Name: {app.config['SENDER_NAME']}")
    logger.info(f"Default Recipient: {app.config['DEFAULT_RECIPIENT_EMAIL']}")
    
    port = int(os.environ.get('PORT', 10000))
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        app.run(host='0.0.0.0', port=port) 