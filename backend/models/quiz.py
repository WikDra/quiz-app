"""
Model danych quizu
"""
import json
import sys
import os
from pathlib import Path

# Konfiguracja ścieżek
module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if module_path not in sys.path:
    sys.path.append(module_path)

from __init__ import db

class Quiz(db.Model):
    """Model reprezentujący quiz w bazie danych"""
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True, index=True)
    difficulty = db.Column(db.String(20), nullable=True, index=True)
    questions_json = db.Column(db.Text, nullable=False)  # Store questions as JSON
    time_limit = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.String(30), nullable=True)
    last_modified = db.Column(db.String(30), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    @property
    def questions(self):
        """Convert JSON string to Python object when accessed"""
        if self.questions_json:
            questions = json.loads(self.questions_json)
            # Upewnij się, że correctAnswer ma poprawny typ int
            for question in questions:
                if 'correctAnswer' in question and question['correctAnswer'] is not None:
                    question['correctAnswer'] = int(question['correctAnswer'])
            return questions
        return []
    
    @questions.setter
    def questions(self, questions_data):
        """Convert Python object to JSON string when set"""
        # Upewnij się, że każde pytanie ma correctAnswer jako int
        for question in questions_data:
            if 'correctAnswer' in question and question['correctAnswer'] is not None:
                question['correctAnswer'] = int(question['correctAnswer'])
        
        self.questions_json = json.dumps(questions_data)
    
    def __repr__(self):
        return f'<Quiz {self.title}>'
    
    def to_dict(self):
        """Konwertuje obiekt Quiz na słownik (dla API)"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'questions': self.questions,
            'timeLimit': self.time_limit,
            'createdAt': self.created_at,
            'lastModified': self.last_modified,
            'userId': self.user_id
        }
