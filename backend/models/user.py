"""
Model danych użytkownika
"""
import sys
import os
from pathlib import Path

# Konfiguracja ścieżek
module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if module_path not in sys.path:
    sys.path.append(module_path)

from __init__ import db

class User(db.Model):
    """Model reprezentujący użytkownika w bazie danych"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    social_id = db.Column(db.String(64), nullable=True)
    social_provider = db.Column(db.String(20), nullable=True)
    
    quizzes = db.relationship('Quiz', backref='author', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Konwertuje obiekt User na słownik (dla API)"""
        return {
            'id': self.id,
            'fullName': self.username,  # Mapowanie username na fullName dla kompatybilności z frontendem
            'email': self.email,
            'isAdmin': self.is_admin,
            'level': 'Początkujący',  # Domyślna wartość
            'stats': {
                'quizzes': 0,
                'bestTime': '0min',
                'correctAnswers': 0
            }
        }
