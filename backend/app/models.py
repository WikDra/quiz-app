from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

from datetime import datetime

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
