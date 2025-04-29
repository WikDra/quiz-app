from app import db
from datetime import datetime
import json

class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True, index=True)
    difficulty = db.Column(db.String(20), nullable=True, index=True)
    questions_json = db.Column(db.Text, nullable=False)  # Store questions as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Quiz {self.title}>'
    
    @property
    def questions(self):
        """Convert JSON string to Python object when accessed"""
        if self.questions_json:
            return json.loads(self.questions_json)
        return []
    
    @questions.setter
    def questions(self, questions_data):
        """Convert Python object to JSON string when set"""
        self.questions_json = json.dumps(questions_data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'questions': self.questions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'user_id': self.user_id
        }
