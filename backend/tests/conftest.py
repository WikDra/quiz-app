"""
Test configuration and fixtures for the quiz-app backend.

This module provides pytest fixtures and configuration for testing
the Flask application with SQLAlchemy models and JWT authentication.
"""

import pytest
import os
import tempfile
from app import create_app
from app.extensions import db
from app.models import User, Quiz, StripeSubscription, OfflinePayment, BlacklistedToken
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import json


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Override configuration for testing
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key-for-jwt',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=30),
        'STRIPE_SECRET_KEY': 'sk_test_test_key',
        'STRIPE_PUBLISHABLE_KEY': 'pk_test_test_key',
        'STRIPE_WEBHOOK_SECRET': 'whsec_test_webhook_secret',
        'GOOGLE_CLIENT_ID': 'test_google_client_id',
        'GOOGLE_CLIENT_SECRET': 'test_google_client_secret',
        'FRONTEND_URL': 'http://localhost:5173'
    }
    
    # Set environment variables for testing
    for key, value in test_config.items():
        os.environ[key] = str(value)
    
    app = create_app()
    app.config.update(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Create a database session for testing."""
    with app.app_context():
        yield db.session
        db.session.rollback()
        # Clean up any test data
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('testpassword'),
        role='user',
        is_admin=False,
        has_premium_access=False
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    admin = User(
        username='admin',
        email='admin@example.com',
        password_hash=generate_password_hash('adminpassword'),
        role='admin',
        is_admin=True,
        has_premium_access=True,
        premium_since=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def premium_user(db_session):
    """Create a premium user for testing."""
    user = User(
        username='premiumuser',
        email='premium@example.com',
        password_hash=generate_password_hash('premiumpassword'),
        role='user',
        is_admin=False,
        has_premium_access=True,
        premium_since=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def oauth_user(db_session):
    """Create an OAuth user for testing."""
    user = User(
        username='OAuth User',
        email='oauth@example.com',
        google_id='123456789',
        social_provider='google',
        avatar_url='https://example.com/avatar.jpg',
        role='user',
        is_admin=False,
        has_premium_access=False
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_quiz(db_session, sample_user):
    """Create a sample quiz for testing."""
    questions = [
        {
            "question": "What is the capital of France?",
            "options": ["London", "Berlin", "Paris", "Madrid"],
            "correct_answer": 2
        },
        {
            "question": "Which planet is closest to the Sun?",
            "options": ["Venus", "Mercury", "Earth", "Mars"],
            "correct_answer": 1
        }
    ]
    
    quiz = Quiz(
        title='Sample Quiz',
        description='A sample quiz for testing',
        category='Geography',
        difficulty='easy',
        author_id=sample_user.id,
        questions_json=json.dumps(questions)
    )
    db_session.add(quiz)
    db_session.commit()
    return quiz


@pytest.fixture
def premium_quiz(db_session, admin_user):
    """Create a premium quiz for testing."""
    questions = [
        {
            "question": "What is the most complex concept in quantum physics?",
            "options": ["Entanglement", "Superposition", "Wave-particle duality", "All of the above"],
            "correct_answer": 3
        }
    ]
    
    quiz = Quiz(
        title='Premium Physics Quiz',
        description='Advanced physics quiz for premium users',
        category='Physics',
        difficulty='hard',
        author_id=admin_user.id,
        questions_json=json.dumps(questions)
    )
    db_session.add(quiz)
    db_session.commit()
    return quiz


@pytest.fixture
def stripe_subscription(db_session, premium_user):
    """Create a Stripe subscription for testing."""
    subscription = StripeSubscription(
        user_id=premium_user.id,
        stripe_subscription_id='sub_test_123',
        stripe_customer_id='cus_test_123',
        status='active',
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
        failed_payment_count=0
    )
    db_session.add(subscription)
    db_session.commit()
    return subscription


@pytest.fixture
def failed_stripe_subscription(db_session, sample_user):
    """Create a failed Stripe subscription for testing."""
    subscription = StripeSubscription(
        user_id=sample_user.id,
        stripe_subscription_id='sub_test_failed',
        stripe_customer_id='cus_test_failed',
        status='past_due',
        current_period_start=datetime.utcnow() - timedelta(days=30),
        current_period_end=datetime.utcnow() - timedelta(days=1),
        failed_payment_count=3
    )
    db_session.add(subscription)
    db_session.commit()
    return subscription


@pytest.fixture
def offline_payment_pending(db_session, sample_user, admin_user):
    """Create a pending offline payment for testing."""
    payment = OfflinePayment(
        user_id=sample_user.id,
        amount=29.99,
        currency='PLN',
        description='Manual payment for premium access',
        admin_id=admin_user.id,
        status='pending',
        payment_method='bank_transfer',
        reference_number='REF123456'
    )
    db_session.add(payment)
    db_session.commit()
    return payment


@pytest.fixture
def offline_payment_approved(db_session, premium_user, admin_user):
    """Create an approved offline payment for testing."""
    payment = OfflinePayment(
        user_id=premium_user.id,
        amount=29.99,
        currency='PLN',
        description='Manual payment for premium access',
        admin_id=admin_user.id,
        status='approved',
        payment_method='cash',
        reference_number='REF789012',
        approved_at=datetime.utcnow(),
        notes='Payment verified and approved'
    )
    db_session.add(payment)
    db_session.commit()
    return payment


@pytest.fixture
def blacklisted_token(db_session, sample_user):
    """Create a blacklisted token for testing."""
    token = BlacklistedToken(
        jti='test-jti-123',
        token_type='access',
        user_id=str(sample_user.id),
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(token)
    db_session.commit()
    return token


@pytest.fixture
def auth_headers(client, sample_user):
    """Generate authentication headers for API testing."""
    response = client.post('/login', json={
        'email': sample_user.email,
        'password': 'testpassword'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    access_token = data['access_token']
    
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Generate admin authentication headers for API testing."""
    response = client.post('/login', json={
        'email': admin_user.email,
        'password': 'adminpassword'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    access_token = data['access_token']
    
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def premium_auth_headers(client, premium_user):
    """Generate premium user authentication headers for API testing."""
    response = client.post('/login', json={
        'email': premium_user.email,
        'password': 'premiumpassword'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    access_token = data['access_token']
    
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


# Helper functions for testing
def create_test_quiz_data():
    """Create test quiz data."""
    return {
        'title': 'Test Quiz',
        'description': 'A test quiz',
        'category': 'Test',
        'difficulty': 'easy',
        'questions': [
            {
                'question': 'Test question?',
                'options': ['A', 'B', 'C', 'D'],
                'correct_answer': 0
            }
        ]
    }


def create_test_user_data():
    """Create test user registration data."""
    return {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpassword123'
    }


def assert_api_error(response, status_code, error_message=None):
    """Assert API error response."""
    assert response.status_code == status_code
    data = response.get_json()
    assert 'error' in data or 'message' in data
    if error_message:
        error_text = data.get('error', data.get('message', ''))
        assert error_message.lower() in error_text.lower()


def assert_api_success(response, status_code=200):
    """Assert API success response."""
    assert response.status_code == status_code
    data = response.get_json()
    assert data is not None
    return data
