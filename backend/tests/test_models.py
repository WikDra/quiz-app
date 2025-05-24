"""
Unit tests for database models.

This module tests all the database models including User, Quiz, 
StripeSubscription, OfflinePayment, and BlacklistedToken.
"""

import pytest
import json
from datetime import datetime, timedelta
from app.models import User, Quiz, StripeSubscription, OfflinePayment, BlacklistedToken
from werkzeug.security import check_password_hash


class TestUserModel:
    """Test cases for the User model."""
    
    def test_user_creation(self, db_session):
        """Test basic user creation."""
        user = User(
            username='testuser',
            email='test@example.com',
            role='user'
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == 'user'
        assert user.is_admin is False
        assert user.has_premium_access is False
        assert user.premium_since is None
        assert user.created_at is not None
    
    def test_password_hashing(self, db_session):
        """Test password hashing and verification."""
        user = User(username='testuser', email='test@example.com')
        password = 'testpassword123'
        
        # Set password
        user.set_password(password)
        assert user.password_hash is not None
        assert user.password_hash != password  # Should be hashed
        
        # Check password
        assert user.check_password(password) is True
        assert user.check_password('wrongpassword') is False
    
    def test_check_password_without_hash(self, db_session):
        """Test password check when no password hash is set."""
        user = User(username='testuser', email='test@example.com')
        assert user.check_password('anypassword') is False
    
    def test_role_management(self, db_session):
        """Test user role management."""
        user = User(username='testuser', email='test@example.com', role='user')
        
        # Test role checking
        assert user.has_role('user') is True
        assert user.has_role('admin') is False
        assert user.is_admin_user() is False
        
        # Promote to admin
        user.promote_to_admin()
        assert user.role == 'admin'
        assert user.is_admin is True
        assert user.is_admin_user() is True
        
        # Demote to user
        user.demote_to_user()
        assert user.role == 'user'
        assert user.is_admin is False
        assert user.is_admin_user() is False
    
    def test_admin_user_creation(self, db_session):
        """Test admin user creation."""
        user = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            is_admin=True
        )
        
        assert user.has_role('admin') is True
        assert user.is_admin_user() is True
    
    def test_oauth_user_creation(self, db_session):
        """Test OAuth user creation."""
        user = User(
            username='OAuth User',
            email='oauth@example.com',
            google_id='123456789',
            social_provider='google',
            avatar_url='https://example.com/avatar.jpg'
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.google_id == '123456789'
        assert user.social_provider == 'google'
        assert user.avatar_url == 'https://example.com/avatar.jpg'
        assert user.password_hash is None  # OAuth users don't have password
    
    def test_user_to_dict(self, db_session):
        """Test user serialization to dictionary."""
        user = User(
            username='testuser',
            email='test@example.com',
            role='user',
            has_premium_access=True,
            premium_since=datetime.utcnow(),
            avatar_url='https://example.com/avatar.jpg'
        )
        db_session.add(user)
        db_session.commit()
        
        user_dict = user.to_dict()
        
        assert user_dict['id'] == user.id
        assert user_dict['username'] == 'testuser'
        assert user_dict['fullName'] == 'testuser'  # Maps to fullName
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['avatar'] == 'https://example.com/avatar.jpg'
        assert user_dict['level'] == 'Początkujący'
        assert user_dict['is_admin'] is False
        assert user_dict['role'] == 'user'
        assert user_dict['has_premium_access'] is True
        assert user_dict['premium_since'] is not None
        assert 'stats' in user_dict
        assert user_dict['created_at'] is not None
    
    def test_user_to_dict_default_avatar(self, db_session):
        """Test user serialization with default avatar."""
        user = User(username='testuser', email='test@example.com')
        db_session.add(user)
        db_session.commit()
        
        user_dict = user.to_dict()
        assert user_dict['avatar'] == 'https://i.pravatar.cc/150?img=3'


class TestQuizModel:
    """Test cases for the Quiz model."""
    
    def test_quiz_creation(self, db_session, sample_user):
        """Test basic quiz creation."""
        quiz = Quiz(
            title='Test Quiz',
            description='A test quiz',
            category='Test',
            difficulty='easy',
            author_id=sample_user.id
        )
        db_session.add(quiz)
        db_session.commit()
        
        assert quiz.id is not None
        assert quiz.title == 'Test Quiz'
        assert quiz.description == 'A test quiz'
        assert quiz.category == 'Test'
        assert quiz.difficulty == 'easy'
        assert quiz.author_id == sample_user.id
        assert quiz.created_at is not None
        assert quiz.updated_at is not None
    
    def test_quiz_with_questions(self, db_session, sample_user):
        """Test quiz creation with questions."""
        questions = [
            {
                "question": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": 1
            },
            {
                "question": "What is the capital of Poland?",
                "options": ["Krakow", "Warsaw", "Gdansk", "Poznan"],
                "correct_answer": 1
            }
        ]
        
        quiz = Quiz(
            title='Math and Geography Quiz',
            description='Test your knowledge',
            category='Mixed',
            difficulty='medium',
            author_id=sample_user.id,
            questions_json=json.dumps(questions)
        )
        db_session.add(quiz)
        db_session.commit()
        
        assert quiz.questions_json is not None
        parsed_questions = json.loads(quiz.questions_json)
        assert len(parsed_questions) == 2
        assert parsed_questions[0]['question'] == "What is 2+2?"
        assert parsed_questions[1]['correct_answer'] == 1
    
    def test_quiz_to_dict(self, db_session, sample_user):
        """Test quiz serialization to dictionary."""
        questions = [{"question": "Test?", "options": ["A", "B"], "correct_answer": 0}]
        
        quiz = Quiz(
            title='Test Quiz',
            description='A test quiz',
            category='Test',
            difficulty='easy',
            author_id=sample_user.id,
            questions_json=json.dumps(questions)
        )
        db_session.add(quiz)
        db_session.commit()
        
        quiz_dict = quiz.to_dict()
        
        assert quiz_dict['id'] == quiz.id
        assert quiz_dict['title'] == 'Test Quiz'
        assert quiz_dict['description'] == 'A test quiz'
        assert quiz_dict['category'] == 'Test'
        assert quiz_dict['difficulty'] == 'easy'
        assert quiz_dict['author_id'] == sample_user.id
        assert quiz_dict['created_at'] is not None
        assert quiz_dict['updated_at'] is not None
        assert 'questions' in quiz_dict
        assert len(quiz_dict['questions']) == 1
        assert quiz_dict['questions'][0]['question'] == "Test?"
    
    def test_quiz_to_dict_empty_questions(self, db_session, sample_user):
        """Test quiz serialization with empty questions."""
        quiz = Quiz(
            title='Empty Quiz',
            author_id=sample_user.id
        )
        db_session.add(quiz)
        db_session.commit()
        
        quiz_dict = quiz.to_dict()
        assert quiz_dict['questions'] == []
    
    def test_quiz_to_dict_invalid_json(self, db_session, sample_user):
        """Test quiz serialization with invalid JSON questions."""
        quiz = Quiz(
            title='Invalid JSON Quiz',
            author_id=sample_user.id,
            questions_json='invalid json{'
        )
        db_session.add(quiz)
        db_session.commit()
        
        quiz_dict = quiz.to_dict()
        assert quiz_dict['questions'] == []  # Should default to empty list


class TestStripeSubscriptionModel:
    """Test cases for the StripeSubscription model."""
    
    def test_subscription_creation(self, db_session, sample_user):
        """Test basic subscription creation."""
        subscription = StripeSubscription(
            user_id=sample_user.id,
            stripe_subscription_id='sub_test_123',
            stripe_customer_id='cus_test_123',
            status='active',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(subscription)
        db_session.commit()
        
        assert subscription.id is not None
        assert subscription.user_id == sample_user.id
        assert subscription.stripe_subscription_id == 'sub_test_123'
        assert subscription.stripe_customer_id == 'cus_test_123'
        assert subscription.status == 'active'
        assert subscription.failed_payment_count == 0  # Default value
        assert subscription.created_at is not None
    
    def test_subscription_with_failed_payments(self, db_session, sample_user):
        """Test subscription with failed payment tracking."""
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
        
        assert subscription.status == 'past_due'
        assert subscription.failed_payment_count == 3
    
    def test_subscription_to_dict(self, db_session, sample_user):
        """Test subscription serialization to dictionary."""
        now = datetime.utcnow()
        subscription = StripeSubscription(
            user_id=sample_user.id,
            stripe_subscription_id='sub_test_123',
            stripe_customer_id='cus_test_123',
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            failed_payment_count=1
        )
        db_session.add(subscription)
        db_session.commit()
        
        sub_dict = subscription.to_dict()
        
        assert sub_dict['id'] == subscription.id
        assert sub_dict['user_id'] == sample_user.id
        assert sub_dict['stripe_subscription_id'] == 'sub_test_123'
        assert sub_dict['stripe_customer_id'] == 'cus_test_123'
        assert sub_dict['status'] == 'active'
        assert sub_dict['failed_payment_count'] == 1
        assert sub_dict['current_period_start'] is not None
        assert sub_dict['current_period_end'] is not None
        assert sub_dict['created_at'] is not None
    
    def test_subscription_user_relationship(self, db_session, sample_user):
        """Test subscription-user relationship."""
        subscription = StripeSubscription(
            user_id=sample_user.id,
            stripe_subscription_id='sub_test_123',
            stripe_customer_id='cus_test_123',
            status='active',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(subscription)
        db_session.commit()
        
        # Test forward relationship
        assert subscription.user == sample_user
        
        # Test backward relationship
        assert sample_user.stripe_subscription == subscription


class TestOfflinePaymentModel:
    """Test cases for the OfflinePayment model."""
    
    def test_offline_payment_creation(self, db_session, sample_user, admin_user):
        """Test basic offline payment creation."""
        payment = OfflinePayment(
            user_id=sample_user.id,
            amount=29.99,
            currency='PLN',
            description='Manual payment',
            admin_id=admin_user.id,
            payment_method='bank_transfer',
            reference_number='REF123'
        )
        db_session.add(payment)
        db_session.commit()
        
        assert payment.id is not None
        assert payment.user_id == sample_user.id
        assert payment.amount == 29.99
        assert payment.currency == 'PLN'
        assert payment.description == 'Manual payment'
        assert payment.admin_id == admin_user.id
        assert payment.status == 'pending'  # Default status
        assert payment.payment_method == 'bank_transfer'
        assert payment.reference_number == 'REF123'
        assert payment.created_at is not None
        assert payment.approved_at is None
    
    def test_approve_payment(self, db_session, sample_user, admin_user):
        """Test payment approval functionality."""
        payment = OfflinePayment(
            user_id=sample_user.id,
            amount=29.99,
            admin_id=admin_user.id
        )
        db_session.add(payment)
        db_session.commit()
        
        # Initially user should not have premium
        assert sample_user.has_premium_access is False
        assert sample_user.premium_since is None
        
        # Approve payment
        admin_notes = "Payment verified and approved"
        payment.approve_payment(admin_notes)
        db_session.commit()
        
        # Check payment status
        assert payment.status == 'approved'
        assert payment.approved_at is not None
        assert payment.notes == admin_notes
        
        # Check user premium status
        assert sample_user.has_premium_access is True
        assert sample_user.premium_since is not None
    
    def test_reject_payment(self, db_session, sample_user, admin_user):
        """Test payment rejection functionality."""
        payment = OfflinePayment(
            user_id=sample_user.id,
            amount=29.99,
            admin_id=admin_user.id
        )
        db_session.add(payment)
        db_session.commit()
        
        # Reject payment
        admin_notes = "Invalid payment proof"
        payment.reject_payment(admin_notes)
        db_session.commit()
        
        # Check payment status
        assert payment.status == 'rejected'
        assert payment.notes == admin_notes
        
        # User should still not have premium
        assert sample_user.has_premium_access is False
    
    def test_offline_payment_to_dict(self, db_session, sample_user, admin_user):
        """Test offline payment serialization to dictionary."""
        payment = OfflinePayment(
            user_id=sample_user.id,
            amount=29.99,
            currency='EUR',
            description='Test payment',
            admin_id=admin_user.id,
            status='approved',
            payment_method='cash',
            reference_number='REF456',
            notes='Test notes'
        )
        payment.approved_at = datetime.utcnow()
        db_session.add(payment)
        db_session.commit()
        
        payment_dict = payment.to_dict()
        
        assert payment_dict['id'] == payment.id
        assert payment_dict['user_id'] == sample_user.id
        assert payment_dict['user_email'] == sample_user.email
        assert payment_dict['user_name'] == sample_user.username
        assert payment_dict['amount'] == 29.99
        assert payment_dict['currency'] == 'EUR'
        assert payment_dict['description'] == 'Test payment'
        assert payment_dict['admin_id'] == admin_user.id
        assert payment_dict['admin_name'] == admin_user.username
        assert payment_dict['status'] == 'approved'
        assert payment_dict['payment_method'] == 'cash'
        assert payment_dict['reference_number'] == 'REF456'
        assert payment_dict['notes'] == 'Test notes'
        assert payment_dict['created_at'] is not None
        assert payment_dict['approved_at'] is not None
    
    def test_offline_payment_relationships(self, db_session, sample_user, admin_user):
        """Test offline payment relationships."""
        payment = OfflinePayment(
            user_id=sample_user.id,
            amount=29.99,
            admin_id=admin_user.id
        )
        db_session.add(payment)
        db_session.commit()
        
        # Test relationships
        assert payment.user == sample_user
        assert payment.admin == admin_user
        assert payment in sample_user.offline_payments


class TestBlacklistedTokenModel:
    """Test cases for the BlacklistedToken model."""
    
    def test_blacklisted_token_creation(self, db_session):
        """Test basic blacklisted token creation."""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = BlacklistedToken(
            jti='test-jti-123',
            token_type='access',
            user_id='123',
            expires_at=expires_at
        )
        db_session.add(token)
        db_session.commit()
        
        assert token.id is not None
        assert token.jti == 'test-jti-123'
        assert token.token_type == 'access'
        assert token.user_id == '123'
        assert token.expires_at == expires_at
        assert token.revoked_at is not None
    
    def test_is_blacklisted_method(self, db_session):
        """Test token blacklist checking."""
        # Token should not be blacklisted initially
        assert BlacklistedToken.is_blacklisted('test-jti-456') is False
        
        # Add token to blacklist
        token = BlacklistedToken(
            jti='test-jti-456',
            token_type='access',
            user_id='123',
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(token)
        db_session.commit()
        
        # Token should now be blacklisted
        assert BlacklistedToken.is_blacklisted('test-jti-456') is True
        assert BlacklistedToken.is_blacklisted('non-existent-jti') is False
    
    def test_cleanup_expired_tokens(self, db_session):
        """Test cleanup of expired blacklisted tokens."""
        # Add expired token
        expired_token = BlacklistedToken(
            jti='expired-jti',
            token_type='access',
            user_id='123',
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        # Add non-expired token
        valid_token = BlacklistedToken(
            jti='valid-jti',
            token_type='access',
            user_id='456',
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        db_session.add(expired_token)
        db_session.add(valid_token)
        db_session.commit()
        
        # Check initial state
        assert BlacklistedToken.query.count() == 2
        
        # Cleanup expired tokens
        deleted_count = BlacklistedToken.cleanup_expired_tokens()
        
        # Check results
        assert deleted_count == 1
        assert BlacklistedToken.query.count() == 1
        assert BlacklistedToken.query.first().jti == 'valid-jti'
    
    def test_blacklisted_token_to_dict(self, db_session):
        """Test blacklisted token serialization to dictionary."""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = BlacklistedToken(
            jti='test-jti-789',
            token_type='refresh',
            user_id='789',
            expires_at=expires_at
        )
        db_session.add(token)
        db_session.commit()
        
        token_dict = token.to_dict()
        
        assert token_dict['id'] == token.id
        assert token_dict['jti'] == 'test-jti-789'
        assert token_dict['token_type'] == 'refresh'
        assert token_dict['user_id'] == '789'
        assert token_dict['revoked_at'] is not None
        assert token_dict['expires_at'] is not None
    
    def test_blacklisted_token_repr(self, db_session):
        """Test blacklisted token string representation."""
        token = BlacklistedToken(
            jti='test-jti-repr',
            token_type='access',
            user_id='123',
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert str(token) == '<BlacklistedToken test-jti-repr>'
