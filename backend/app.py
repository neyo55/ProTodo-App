# app.py
# ProTodo Backend v1.0 (Development Build)
# Features: JWT Auth (Debug enabled), 3-Minute Reminder Window, SQLite

from flask import Blueprint, Flask, jsonify
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

    # === CORS: Allow all origins (Development) ===
    CORS(app, origins=["*"], supports_credentials=True)

    db.init_app(app)
    
    # === JWT CONFIGURATION ===
    jwt = JWTManager(app)

    # Error Handlers for Token Issues (Fixes 422 Mysteries)
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"❌ INVALID TOKEN ERROR: {error}") 
        return jsonify({"message": "Invalid token", "error": error}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"❌ MISSING TOKEN ERROR: {error}")
        return jsonify({"message": "Missing token", "error": error}), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print(f"❌ EXPIRED TOKEN: {jwt_payload}")
        return jsonify({"message": "Token expired", "error": "token_expired"}), 401

    # === REGISTER BLUEPRINTS ===
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(todos_bp, url_prefix='/api')

    @app.route('/')
    def home():
        return "ProTodo Backend v1.0 Running!"

    # === SCHEDULER: 3-MINUTE REMINDERS ===
    scheduler = APScheduler()
    scheduler.init_app(app)

    # Check every 1 minute to catch tasks falling into the 3-minute window
    @scheduler.task('interval', id='check_reminders', minutes=1)
    def check_due_reminders():
        with app.app_context():
            # 1. Get current UTC time
            now = datetime.now(timezone.utc)
            
            # 2. Define Window: Tasks due between NOW and NOW + 3 MINUTES
            notification_window = now + timedelta(minutes=3)
            
            # 3. Find Tasks
            due_todos = Todo.query.filter(
                Todo.due_date <= notification_window, # Due in next 3 mins
                Todo.due_date >= now,                 # Not in the past
                Todo.completed == False,
                Todo.reminder_sent == False
            ).all()

            if not due_todos:
                return # Keep logs clean if nothing to send

            print(f"\n[{now}] Found {len(due_todos)} tasks due in next 3 mins...")

            for todo in due_todos:
                # FIX: Use db.session.get() to avoid Legacy Warning
                user = db.session.get(User, todo.user_id)

                if not user or not user.email:
                    continue

                print(f"📧 Sending reminder for '{todo.title}' to {user.email}...")
                
                success = send_reminder_email(
                    to_email=user.email,
                    todo_title=todo.title,
                    due_date_str=todo.due_date.strftime('%Y-%m-%d %H:%M')
                )

                if success:
                    todo.reminder_sent = True
                    db.session.commit()
                    print(f"  ✅ Sent!")
                else:
                    print(f"  ❌ Failed to send email.")

    scheduler.start()

    # Create tables
    with app.app_context():
        db.create_all()
        print("Database tables ready!")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5000, debug=True)







# # app.py
# # Main Flask application for ProTodo
# # Updated: Jan 04, 2026
# # Features: JWT Debugging (Fixes 422), Test Mode Email Scheduler

# from flask import Flask, jsonify
# from flask_cors import CORS
# from flask_jwt_extended import JWTManager
# from config import Config
# from models import db, User, Todo
# from auth import auth_bp
# from todos import todos_bp
# from mailer import send_reminder_email
# from datetime import datetime, timezone
# from flask_apscheduler import APScheduler

# def create_app():
#     app = Flask(__name__)
#     app.config.from_object(Config)

#     # === CORS: Allow all origins (Fixes connection issues) ===
#     CORS(app, origins=["*"], supports_credentials=True)

#     db.init_app(app)
    
#     # === JWT CONFIGURATION WITH DEBUGGING ===
#     jwt = JWTManager(app) # Assign to 'jwt' variable to add callbacks

#     # 1. Prints why the token is invalid (e.g. "Signature verification failed")
#     @jwt.invalid_token_loader
#     def invalid_token_callback(error):
#         print(f"❌ INVALID TOKEN ERROR: {error}") 
#         return jsonify({"message": "Invalid token", "error": error}), 422

#     # 2. Prints if no token was sent at all
#     @jwt.unauthorized_loader
#     def missing_token_callback(error):
#         print(f"❌ MISSING TOKEN ERROR: {error}")
#         return jsonify({"message": "Missing token", "error": error}), 401
    
#     # 3. Prints if the token is expired
#     @jwt.expired_token_loader
#     def expired_token_callback(jwt_header, jwt_payload):
#         print(f"❌ EXPIRED TOKEN: {jwt_payload}")
#         return jsonify({"message": "Token expired", "error": "token_expired"}), 401

#     # === REGISTER BLUEPRINTS ===
#     # All routes under /api (e.g., /api/login, /api/todos)
#     app.register_blueprint(auth_bp, url_prefix='/api')
#     app.register_blueprint(todos_bp, url_prefix='/api')

#     @app.route('/')
#     def home():
#         return "ProTodo Backend Running! Debug Mode Active."

#     # === GMAIL REMINDER SCHEDULER (TEST MODE) ===
#     scheduler = APScheduler()
#     scheduler.init_app(app)

#     # Check every 1 minute for immediate testing
#     @scheduler.task('interval', id='check_reminders', minutes=1)
#     def check_due_reminders():
#         with app.app_context():
#             print(f"\n[{datetime.now(timezone.utc)}] === SCHEDULER CHECKING REMINDERS ===")

#             # TEST MODE: Find ANY incomplete todo that has a due date
#             # and has NOT received an email yet.
#             due_todos = Todo.query.filter(
#                 Todo.due_date.isnot(None),      # Has a due date
#                 Todo.completed == False,        # Not finished
#                 Todo.reminder_sent == False     # Email not sent yet
#             ).all()

#             if not due_todos:
#                 print("No pending emails to send.")
            
#             for todo in due_todos:
#                 user = User.query.get(todo.user_id)
#                 if not user or not user.email:
#                     print(f"Skipping Todo {todo.id}: No user email found.")
#                     continue

#                 print(f"📧 Sending email to {user.email} for task '{todo.title}'...")
                
#                 # Send the email
#                 success = send_reminder_email(
#                     to_email=user.email,
#                     todo_title=todo.title,
#                     due_date_str=todo.due_date.strftime('%Y-%m-%d %H:%M')
#                 )

#                 if success:
#                     # IMPORTANT: Mark as sent so we don't spam the user
#                     todo.reminder_sent = True 
#                     db.session.commit()
#                     print(f"  ✅ SUCCESS! Email sent and database updated.")
#                 else:
#                     print(f"  ❌ FAILED. Check your .env GMAIL_USER and GMAIL_APP_PASSWORD.")

#     scheduler.start()

#     # Create tables if they don't exist
#     with app.app_context():
#         db.create_all()
#         print("Database tables ready!")

#     return app

# if __name__ == '__main__':
#     app = create_app()
#     app.run(port=5000, debug=True)