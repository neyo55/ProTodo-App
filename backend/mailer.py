# email.py - Send reminder emails using Gmail SMTP (development only)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_reminder_email(to_email, todo_title, due_date_str):
    """
    Send a simple reminder email via Gmail SMTP
    NOTE: For development only! Use Brevo/SendGrid in production
    """
    # === CONFIGURE THESE IN .env ===
    gmail_user = os.getenv('GMAIL_USER')      # e.g., yourname@gmail.com
    gmail_pass = os.getenv('GMAIL_APP_PASSWORD')  # App password, NOT regular password!

    if not gmail_user or not gmail_pass:
        print("Warning: Gmail credentials not set. Skipping email.")
        return False

    subject = f"Reminder: '{todo_title}' is due!"
    body = f"""
    Hi there!

    This is a friendly reminder that your todo is due:

    📌 Task: {todo_title}
    ⏰ Due: {due_date_str}

    Log in to ProTodo to mark it complete or update it.

    Have a productive day! 🚀
    """

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, to_email, msg.as_string())
        server.quit()
        print(f"Reminder email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False