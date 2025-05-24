from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
from flask import current_app
from datetime import datetime, timedelta

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    difficulty = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationship with questions (using JSON for simplicity in this version)
    questions_json = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        """Convert quiz to dictionary"""
        import json
        
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'author_id': self.author_id
        }
        
        # Parse questions from JSON
        if self.questions_json:
            try:
                result['questions'] = json.loads(self.questions_json)
            except:
                result['questions'] = []
        else:
            result['questions'] = []
            
        return result
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stripe_payment_intent_id = db.Column(db.String(100), nullable=False, unique=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Payment {self.stripe_payment_intent_id} - {self.status}>"
    
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    google_id = db.Column(db.String(100), nullable=True, unique=True)
    social_provider = db.Column(db.String(20), nullable=True)
    has_premium_access = db.Column(db.Boolean, default=False) # Add premium access field
    premium_since = db.Column(db.DateTime, nullable=True) # Track when premium was activated

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
        
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'fullName': self.username,  # Map username to fullName for frontend compatibility
            'email': self.email,
            'avatar': self.avatar_url or 'https://i.pravatar.cc/150?img=3',  # Default avatar
            'level': 'Początkujący',  # Default level            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'has_premium_access': self.has_premium_access, # Include in dict
            'premium_since': self.premium_since.isoformat() if self.premium_since else None,
            'stats': {
                'quizzes': 0,
                'bestTime': '0min',
                'correctAnswers': 0
            }
        }

class StripeSubscription(db.Model):
    __tablename__ = 'stripe_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(255), unique=True)
    stripe_customer_id = db.Column(db.String(255), unique=True)
    status = db.Column(db.String(50), nullable=False)  # active, canceled, past_due
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    canceled_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('stripe_subscription', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'stripe_customer_id': self.stripe_customer_id,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None
        }

class BlacklistedToken(db.Model):
    """
    Model for storing blacklisted JWT tokens to prevent their reuse after logout
    """
    __tablename__ = 'blacklisted_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)  # JWT ID (unique identifier)
    token_type = db.Column(db.String(10), nullable=False)  # 'access' or 'refresh'
    user_id = db.Column(db.String(100), nullable=False)  # Changed to String to handle large OAuth IDs
    revoked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)  # When the token would naturally expire
    
    def __init__(self, jti, token_type, user_id, expires_at):
        self.jti = jti
        self.token_type = token_type
        self.user_id = user_id
        self.expires_at = expires_at
    
    def __repr__(self):
        return f'<BlacklistedToken {self.jti}>'
    
    @staticmethod
    def is_blacklisted(jti):
        """Check if a token is blacklisted"""
        return BlacklistedToken.query.filter_by(jti=jti).first() is not None
    
    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired blacklisted tokens from database"""
        expired_tokens = BlacklistedToken.query.filter(
            BlacklistedToken.expires_at < datetime.utcnow()
        ).all()
        
        for token in expired_tokens:
            db.session.delete(token)
        
        db.session.commit()
        return len(expired_tokens)

    def to_dict(self):
        return {
            'id': self.id,
            'jti': self.jti,
            'token_type': self.token_type,
            'user_id': self.user_id,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

def _process_subscription_by_email(customer_email, session):
    """Helper function to process subscription by email"""
    user = User.query.filter_by(email=customer_email).first()
    if user:
        subscription = StripeSubscription.query.filter_by(user_id=user.id).first()
        
        if not subscription:
            subscription = StripeSubscription(
                user_id=user.id,
                stripe_customer_id=session.get('customer'),
                stripe_subscription_id=session.get('subscription'),
                status='active',
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(subscription)
        else:
            subscription.status = 'active'
            subscription.stripe_customer_id = session.get('customer')
            subscription.stripe_subscription_id = session.get('subscription')
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
        
        user.has_premium_access = True
        if not user.premium_since:
            user.premium_since = datetime.utcnow()
        
        db.session.commit()
        current_app.logger.info(f"Subscription created/updated for user {user.id} (via email)")
    else:
        current_app.logger.warning(f"User with email {customer_email} not found after payment.")