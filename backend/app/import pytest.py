import pytest
from flask import json
from .routes import RegisterResource, LoginResource
from .models import User
from .extensions import db

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_database(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

class TestRegisterResource:
    def test_successful_registration(self, client, init_database):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = client.post('/api/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        assert b'Registration successful' in response.data
        assert 'access_token_cookie' in response.cookies
        assert 'refresh_token_cookie' in response.cookies

    def test_registration_missing_data(self, client):
        response = client.post('/api/register',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        assert b'No data provided' in response.data

    def test_registration_existing_username(self, client, init_database):
        # First registration
        data = {
            'username': 'existinguser',
            'email': 'existing@example.com',
            'password': 'testpass123'
        }
        client.post('/api/register',
                   data=json.dumps(data),
                   content_type='application/json')

        # Second registration with same username
        response = client.post('/api/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 409
        assert b'already exists' in response.data.lower()

class TestLoginResource:
    def test_successful_login(self, client, init_database):
        # Register user first
        user_data = {
            'username': 'logintest',
            'email': 'login@example.com',
            'password': 'testpass123'
        }
        client.post('/api/register',
                   data=json.dumps(user_data),
                   content_type='application/json')

        # Try logging in
        login_data = {
            'username': 'logintest',
            'password': 'testpass123'
        }
        response = client.post('/api/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        assert 'access_token_cookie' in response.cookies
        assert 'refresh_token_cookie' in response.cookies

    def test_login_invalid_credentials(self, client):
        login_data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        response = client.post('/api/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        assert b'Invalid credentials' in response.data

    def test_login_missing_data(self, client):
        response = client.post('/api/login',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        assert b'No JSON data provided' in response.data

    def test_login_missing_password(self, client):
        login_data = {'username': 'testuser'}
        response = client.post('/api/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        assert b'Username and password are required' in response.data