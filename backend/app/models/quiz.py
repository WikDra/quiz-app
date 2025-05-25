"""Quiz model definition."""

from ..extensions import db
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
