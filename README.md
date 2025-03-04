# 📅 Reminder App

A modern, production-ready web application for managing reminders with automated email notifications.

## ✨ Features

- 📧 Email notifications for reminders
- 🔄 Multiple frequency options (once, daily, weekly, monthly, yearly)
- 📊 CSV import/export functionality
- 🎯 Real-time updates
- 🔒 Secure email handling
- 🚀 Production-ready with Redis and Celery
- 📱 Responsive design

## 🛠️ Tech Stack

- **Backend**: Flask, Celery
- **Database**: PostgreSQL
- **Task Queue**: Redis
- **Email**: SMTP (Gmail)
- **Frontend**: HTML5, CSS3, JavaScript
- **Deployment**: Render.com

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/reminder-app.git
cd reminder-app
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
SENDER_NAME=Reminder App
DEFAULT_RECIPIENT_EMAIL=default@email.com
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/reminder
REDIS_URL=redis://localhost:6379/0
```

5. Initialize the database:
```bash
flask db upgrade
```

## 🏃‍♂️ Running the App

### Development

1. Start Redis:
```bash
redis-server
```

2. Start Celery worker:
```bash
celery -A tasks.celery worker --loglevel=info
```

3. Start Celery beat:
```bash
celery -A tasks.celery beat --loglevel=info
```

4. Run the Flask application:
```bash
python app.py
```

### Production

The app is configured for deployment on Render.com with:
- PostgreSQL database
- Redis for task queue
- Celery for background tasks
- Gunicorn as WSGI server

## 📝 API Documentation

### Endpoints

- `GET /get_reminders` - List all reminders
- `POST /add_reminder` - Create a new reminder
- `PUT /edit_reminder/<id>` - Update a reminder
- `DELETE /delete_reminder/<id>` - Delete a reminder
- `POST /test_email` - Test email configuration
- `GET /sample_csv` - Download CSV template
- `POST /upload_csv` - Import reminders via CSV
- `POST /reset_database` - Reset the database
- `GET /health` - Check application health

## 🔧 Configuration

The app uses a hierarchical configuration system:
- `config.py` - Main configuration file
- `.env` - Environment variables
- `gunicorn_config.py` - Gunicorn server settings
- `render.yaml` - Render.com deployment configuration

## 🏗️ Project Structure

## 🎯 Why Choose Reminder App?

- **Effortless Organization**: Keep track of important dates and events with ease.
- **Reliable Notifications**: Never miss a reminder with email alerts.
- **Efficient Management**: Use CSV uploads for bulk reminder management.
- **Customizable Frequency**: Set reminders to repeat at your desired intervals.
- **User-Friendly Interface**: Navigate with ease on any device.

## 🤝 Contributing

We welcome contributions! Fork the repository and submit a pull request to contribute.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Thank you for using the Reminder App! We hope it enhances your productivity and keeps you on schedule. For questions or feedback, feel free to reach out.
