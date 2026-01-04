# models.py
# Database models for ProTodo app using Flask-SQLAlchemy
# Uses SQLite locally, ready for MySQL on production

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)  # Optional name
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: One user has many todos
    todos = db.relationship('Todo', backref='owner', lazy=True, cascade='all, delete-orphan')

    # Securely hash password
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Verify password
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def __repr__(self):
        return f'<User {self.email}>'


class Todo(db.Model):
    __tablename__ = 'todo'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)  # Accepts datetime-local input
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    category = db.Column(db.String(50), default='other')   # work, personal, etc.
    tags = db.Column(db.Text, nullable=True)               # Stored as comma-separated string
    notes = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    
    # === NEW: Tracks if the email reminder was already sent to avoid spam ===
    reminder_sent = db.Column(db.Boolean, default=False) 
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Todo {self.title[:30]}...>'