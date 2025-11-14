from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DATABASE = 'todos.db'

def get_db():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with todos table"""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

with app.app_context():
    init_db()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/todos', methods=['GET'])
def get_todos():
    """Get all todos"""
    conn = get_db()
    todos = conn.execute('SELECT * FROM todos ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(todo) for todo in todos]), 200

@app.route('/api/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Get a specific todo by ID"""
    conn = get_db()
    todo = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    conn.close()
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(dict(todo)), 200

@app.route('/api/todos', methods=['POST'])
def create_todo():
    """Create a new todo"""
    data = request.get_json()

    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400

    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO todos (title, description, completed) VALUES (?, ?, ?)',
        (data['title'], data.get('description', ''), data.get('completed', False))
    )
    conn.commit()
    todo_id = cursor.lastrowid
    conn.close()

    return jsonify({'id': todo_id, 'message': 'Todo created successfully'}), 201

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """Update an existing todo"""
    data = request.get_json()

    conn = get_db()
    todo = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()

    if todo is None:
        conn.close()
        return jsonify({'error': 'Todo not found'}), 404

    title = data.get('title', todo['title'])
    description = data.get('description', todo['description'])
    completed = data.get('completed', todo['completed'])

    conn.execute(
        'UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?',
        (title, description, completed, todo_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Todo updated successfully'}), 200


@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a todo"""
    conn = get_db()
    result = conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    conn.commit()

    if result.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Todo not found'}), 404

    conn.close()
    return jsonify({'message': 'Todo deleted successfully'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
