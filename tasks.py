from celery import Celery
from app import app, db, Reminder, send_email
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@celery.task
def check_reminders():
    """Check for due reminders and send notifications"""
    try:
        now = datetime.utcnow()
        reminders = Reminder.query.filter(
            (Reminder.end_date.is_(None) | (Reminder.end_date >= now))
        ).all()

        for reminder in reminders:
            process_reminder.delay(reminder.id, now)
            
    except Exception as e:
        logger.error(f"Error in check_reminders: {str(e)}")

@celery.task
def process_reminder(reminder_id, current_time):
    """Process individual reminder"""
    try:
        reminder = Reminder.query.get(reminder_id)
        if not reminder:
            return

        should_send = should_send_reminder(reminder, current_time)
        
        if should_send:
            subject = f"Reminder: {reminder.description}"
            body = create_reminder_email_body(reminder)
            
            if send_email(reminder.email, subject, body):
                reminder.last_sent = current_time
                db.session.commit()
                logger.info(f"Reminder sent for ID: {reminder_id}")
            else:
                logger.error(f"Failed to send reminder for ID: {reminder_id}")
                
    except Exception as e:
        logger.error(f"Error processing reminder {reminder_id}: {str(e)}")

def should_send_reminder(reminder, current_time):
    """Determine if reminder should be sent"""
    if reminder.last_sent is None:
        return reminder.date <= current_time
        
    if reminder.frequency == "once":
        return reminder.date <= current_time and not reminder.last_sent
        
    time_since_last = current_time - reminder.last_sent
    
    if reminder.frequency == "daily":
        return time_since_last.days >= 1
    elif reminder.frequency == "weekly":
        return time_since_last.days >= 7
    elif reminder.frequency == "monthly":
        next_date = reminder.last_sent.replace(month=reminder.last_sent.month + 1)
        return current_time >= next_date
    elif reminder.frequency == "yearly":
        next_date = reminder.last_sent.replace(year=reminder.last_sent.year + 1)
        return current_time >= next_date
        
    return False

def create_reminder_email_body(reminder):
    """Create email body for reminder"""
    return f"""
    Hello!

    This is your {reminder.frequency} reminder for: {reminder.description}
    Originally scheduled for: {reminder.date.strftime('%d-%m-%Y %H:%M')}

    Frequency: {reminder.frequency.capitalize()}
    {f"End Date: {reminder.end_date.strftime('%d-%m-%Y')}" if reminder.end_date else ""}

    Best regards,
    {app.config['SENDER_NAME']}
    """ 