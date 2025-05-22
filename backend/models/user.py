"""
User model definition
"""
from datetime import datetime
from flask_bcrypt import generate_password_hash, check_password_hash
from models import db

class InvalidToken(db.Model):
    """Store invalidated/blacklisted tokens"""
    __tablename__ = 'invalid_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    type = db.Column(db.String(16), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @classmethod
    def is_token_revoked(cls, jti):
        """Check if a token is in the blacklist"""
        return cls.query.filter_by(jti=jti).first() is not None

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    social_id = db.Column(db.String(100), nullable=True, unique=True)
    social_provider = db.Column(db.String(20), nullable=True)
    has_premium_access = db.Column(db.Boolean, default=False) # Add premium access field
    premium_since = db.Column(db.DateTime, nullable=True) # Track when premium was activated

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password).decode('utf-8')
        
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
