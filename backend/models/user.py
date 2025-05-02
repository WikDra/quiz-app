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

from __init__ import db, bcrypt

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
    avatar_url = db.Column(db.String(255), nullable=True)
    
    quizzes = db.relationship('Quiz', backref='author', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Haszuje i ustawia hasło użytkownika"""
        if password:
            self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Sprawdza, czy podane hasło jest prawidłowe"""
        if not self.password_hash or not password:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_default_avatar(self):
        """Generuje domyślny awatar bazujący na emailu użytkownika (używając Gravatar)"""
        import hashlib
        
        # Użyj adresu email do wygenerowania Gravatar URL
        email_lower = self.email.lower().strip()
        email_hash = hashlib.md5(email_lower.encode('utf-8')).hexdigest()
        
        # Generuj URL Gravatar
        return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s=200"
    
    def to_dict(self):
        """Konwertuje obiekt User na słownik (dla API)"""
        return {
            'id': self.id,
            'fullName': self.username,  # Mapowanie username na fullName dla kompatybilności z frontendem
            'email': self.email,
            'isAdmin': self.is_admin,
            'level': 'Początkujący',  # Domyślna wartość
            'avatar': self.avatar_url or self.get_default_avatar(),  # Użyj własnego URL lub domyślnego awatara
            'stats': {
                'quizzes': 0,
                'bestTime': '0min',
                'correctAnswers': 0
            }
        }
