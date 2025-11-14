import pytest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, init_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200

def test_create_todo(client):
    response = client.post('/api/todos',
                          data=json.dumps({'title': 'Test'}),
                          content_type='application/json')
    assert response.status_code == 201

def test_get_todos(client):
    response = client.get('/api/todos')
    assert response.status_code == 200
