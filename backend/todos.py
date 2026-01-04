# todos.py
# Todo CRUD API routes for ProTodo app
# Updated to handle String vs Integer JWT identities

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Todo
from datetime import datetime, timezone, timedelta

# Blueprint without url_prefix — registered under /api in app.py
todos_bp = Blueprint('todos', __name__)


# === GET all todos ===
@todos_bp.route('/todos', methods=['GET'])
@jwt_required()
def get_todos():
    # FIXED: Convert string identity back to integer for database query
    user_id = int(get_jwt_identity())
    print(f"[GET /api/todos] Request from user ID: {user_id}")

    user_todos = Todo.query.filter_by(user_id=user_id)\
        .order_by(Todo.created_at.desc())\
        .all()

    return jsonify([todo_to_dict(todo) for todo in user_todos]), 200


# === CREATE a new todo ===
@todos_bp.route('/todos', methods=['POST'])
@jwt_required()
def add_todo():
    # FIXED: Convert string identity back to integer
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    print("\n=== NEW TODO CREATION REQUEST ===")
    
    if not data.get('title'):
        return jsonify({"message": "Title is required"}), 400

    # Parse due date
    raw_due = data.get('due_date')
    parsed_due = parse_due_date(raw_due)

    new_todo = Todo(
        title=data.get('title', '').strip(),
        due_date=parsed_due,
        priority=data.get('priority', 'medium').lower(),
        category=data.get('category', 'other').lower(),
        tags=','.join([t.strip() for t in data.get('tags', []) if t.strip()]) or None,
        notes=data.get('notes', '').strip() or None,
        completed=data.get('completed', False),
        user_id=user_id,
        reminder_sent=False
    )

    try:
        db.session.add(new_todo)
        db.session.commit()
        print(f"SUCCESS: Todo created with ID {new_todo.id}")
        return jsonify(todo_to_dict(new_todo)), 201
    except Exception as e:
        db.session.rollback()
        print(f"DATABASE ERROR: {e}")
        return jsonify({"message": "Failed to save todo"}), 500


# === UPDATE an existing todo ===
@todos_bp.route('/todos/<int:todo_id>', methods=['PUT'])
@jwt_required()
def update_todo(todo_id):
    user_id = int(get_jwt_identity()) # Fixed
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first_or_404()

    data = request.get_json(silent=True) or {}

    if 'title' in data: todo.title = data['title'].strip()
    if 'completed' in data: todo.completed = bool(data['completed'])
    if 'due_date' in data: 
        todo.due_date = parse_due_date(data['due_date'])
        todo.reminder_sent = False
    if 'priority' in data: todo.priority = data['priority'].lower()
    if 'category' in data: todo.category = data['category'].lower()
    if 'tags' in data:
        tags = [t.strip() for t in data.get('tags', []) if t.strip()]
        todo.tags = ','.join(tags) if tags else None
    if 'notes' in data: todo.notes = data['notes'].strip() if data['notes'] else None

    try:
        db.session.commit()
        return jsonify(todo_to_dict(todo)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Update failed"}), 500


# === DELETE a todo ===
@todos_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def delete_todo(todo_id):
    user_id = int(get_jwt_identity()) # Fixed
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first_or_404()

    try:
        db.session.delete(todo)
        db.session.commit()
        return jsonify({"message": "Deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Delete failed"}), 500


# === HELPER: Convert frontend local time to UTC ===
def parse_due_date(date_str):
    if not date_str or date_str in ('null', 'undefined', ''):
        return None
    try:
        naive_dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        # Adjust for Nigeria (WAT = UTC+1)
        return (naive_dt - timedelta(hours=1)).replace(tzinfo=timezone.utc)
    except:
        return None

def todo_to_dict(todo):
    return {
        "id": todo.id,
        "title": todo.title,
        "due_date": todo.due_date.strftime('%Y-%m-%dT%H:%M') if todo.due_date else None,
        "priority": todo.priority,
        "category": todo.category,
        "tags": todo.tags.split(',') if todo.tags else [],
        "notes": todo.notes,
        "completed": todo.completed,
        "created_at": todo.created_at.isoformat()
    }