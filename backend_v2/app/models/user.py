from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    # Profile info
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    
    # OAuth fields
    google_id = db.Column(db.String(100), unique=True)
    is_oauth_user = db.Column(db.Boolean, default=False)
    
    # Premium status
    is_premium = db.Column(db.Boolean, default=False)
    premium_expires_at = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    quizzes = db.relationship('Quiz', backref='creator', lazy=True)
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Return user ID as string for Flask-Login"""
        return str(self.id)
    
    @property
    def is_active(self):
        """Return True if user is active"""
        return True
    
    @property
    def is_authenticated(self):
        """Return True if user is authenticated"""
        return True
    
    @property
    def is_anonymous(self):
        """Return False as this is not an anonymous user"""
        return False
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary for JSON response"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_premium': self.is_premium,
            'premium_expires_at': self.premium_expires_at.isoformat() if self.premium_expires_at else None,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
