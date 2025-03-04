# 📅 Reminder App

**Stay organized and never miss a beat with the Reminder App!** This intuitive web application helps you manage your reminders effortlessly, with features like recurring notifications, email alerts, and bulk uploads.

## 🚀 Features

- **Single & Recurring Reminders**: Set reminders for one-time or recurring events (daily, weekly, monthly, yearly).
- **Email Alerts**: Receive timely email notifications for all your reminders.
- **CSV Bulk Upload**: Easily upload multiple reminders using a CSV file.
- **Test Email Functionality**: Ensure your email settings are correctly configured.
- **Responsive Design**: Enjoy a seamless experience on any device.

## 🛠️ Quick Start

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/reminder-app.git
   cd reminder-app
   ```

2. **Configure Environment**:
   - Create a `.env` file with your email settings:
     ```plaintext
     SMTP_SERVER=smtp.gmail.com
     SMTP_PORT=587
     SMTP_USERNAME=your.email@gmail.com
     SMTP_PASSWORD=your-app-password
     SENDER_EMAIL=your.email@gmail.com
     SENDER_NAME=Reminder App
     DEFAULT_RECIPIENT_EMAIL=default.recipient@gmail.com
     ```

3. **Install Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```

5. **Access the App**:
   - Open your browser and visit `http://localhost:5001`.

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
