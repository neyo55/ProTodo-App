# app.py
# ProTodo Backend v1.0 (Production Stable)
# Features: JWT Auth, 3-Minute Reminder Window, Crash-Resistant Scheduler

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db, User, Todo
from auth import auth_bp
from todos import todos_bp
from mailer import send_reminder_email
from datetime import datetime, timezone, timedelta
from flask_apscheduler import APScheduler

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # === CORS CONFIGURATION ===
    # Allows the frontend (running on a different port/domain) to talk to this backend
    # supports_credentials=True is required for sending cookies/auth headers
    CORS(app, origins=["*"], supports_credentials=True)

    # === DATABASE INITIALIZATION ===
    db.init_app(app)
    
    # === JWT AUTHENTICATION SETUP ===
    jwt = JWTManager(app)

    # --- JWT Error Handlers (Helpful for Debugging) ---
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"❌ INVALID TOKEN ERROR: {error}") 
        return jsonify({"message": "Invalid token", "error": str(error)}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"❌ MISSING TOKEN ERROR: {error}")
        return jsonify({"message": "Missing token", "error": str(error)}), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print(f"❌ EXPIRED TOKEN: {jwt_payload}")
        return jsonify({"message": "Token expired", "error": "token_expired"}), 401

    # === REGISTER API ROUTES (BLUEPRINTS) ===
    # All routes will start with /api (e.g., /api/login, /api/todos)
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(todos_bp, url_prefix='/api')

    @app.route('/')
    def home():
        return "ProTodo Backend v1.1 Running!"

    # === BACKGROUND SCHEDULER: EMAIL REMINDERS ===
    # This runs in the background to check for tasks due soon.
    scheduler = APScheduler()
    scheduler.init_app(app)

    # Task: Run every 1 minute
    @scheduler.task('interval', id='check_reminders', minutes=1)
    def check_due_reminders():
        with app.app_context():
            # 1. Get current UTC time (Standard for all servers)
            now = datetime.now(timezone.utc)
            
            # 2. Define the "Window": Tasks due between NOW and NOW + 3 MINUTES
            notification_window = now + timedelta(minutes=3)
            
            # 3. Query Database for matching tasks
            # Criteria: Due soon, Not in past, Not completed, No email sent yet
            due_todos = Todo.query.filter(
                Todo.due_date <= notification_window, 
                Todo.due_date >= now,                 
                Todo.completed == False,
                Todo.reminder_sent == False
            ).all()

            if not due_todos:
                return # Exit if nothing to do (keeps logs clean)

            print(f"\n[{now}] 🔔 Found {len(due_todos)} tasks due in next 3 mins...")

            for todo in due_todos:
                # Use db.session.get() to avoid SQLAlchemy Legacy Warnings
                user = db.session.get(User, todo.user_id)

                if not user or not user.email:
                    continue

                print(f"📧 Sending reminder for '{todo.title}' to {user.email}...")
                
                # Send the email using mailer.py logic
                success = send_reminder_email(
                    to_email=user.email,
                    todo_title=todo.title,
                    due_date_str=todo.due_date.strftime('%Y-%m-%d %H:%M')
                )

                # 4. Mark as sent so we don't spam the user every minute
                if success:
                    todo.reminder_sent = True
                    db.session.commit()
                    print(f"  ✅ Sent successfully!")
                else:
                    print(f"  ❌ Failed to send email.")

    # === CRITICAL FIX FOR GUNICORN CRASHES ===
    # When running with multiple workers (Gunicorn), each worker tries to start the scheduler.
    # This causes them to fight over the Database Connection ("Packet sequence number wrong").
    # We wrap .start() in a try-except block so if one fails, the worker stays alive.
    try:
        scheduler.start()
        print("✅ Scheduler started successfully.")
    except Exception as e:
        print(f"⚠️ Scheduler failed to start (Ignoring to prevent crash): {e}")

    # === DATABASE TABLE CREATION ===
    # Automatically creates tables if they don't exist
    with app.app_context():
        db.create_all()
        print("💾 Database tables verified/created!")

    return app

if __name__ == '__main__':
    app = create_app()
    # NOTE: debug=True is DANGEROUS in production.
    # We removed it here. Use the .env file variable FLASK_DEBUG=1 for local testing.
    app.run(port=5000)