"""
Skrypt do inicjalizacji kompletnej bazy danych SQLite i importu danych z plików JSON.
Ten skrypt wykonuje wszystkie operacje potrzebne do przygotowania bazy danych.
"""
import os
import sys
import json
from pathlib import Path
import traceback

# Dodaj katalog główny projektu do ścieżki Pythona
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Tworzenie Flask app i db z poprawnym kontekstem
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

# Lokalizacja plików
PROJECT_ROOT = BASE_DIR.parent
QUIZ_JSON_PATH = PROJECT_ROOT / 'public' / 'quiz.json'
USERS_JSON_PATH = PROJECT_ROOT / 'public' / 'users.json'

# Tworzenie aplikacji Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_key_for_quiz_app'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{BASE_DIR / "quiz_app.db"}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicjalizacja rozszerzeń
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

# Definicje modeli
class User(db.Model):
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

class Quiz(db.Model):
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
            return json.loads(self.questions_json)
        return []
    
    @questions.setter
    def questions(self, questions_data):
        """Convert Python object to JSON string when set"""
        self.questions_json = json.dumps(questions_data)
    
    def __repr__(self):
        return f'<Quiz {self.title}>'

def load_json_data(file_path):
    """Wczytuje dane z pliku JSON, obsługując komentarze na początku pliku"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Usuń komentarz z początku pliku jeśli istnieje
        if content.strip().startswith('//'):
            content = '\n'.join(content.splitlines()[1:])
            
        return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Błąd odczytu pliku {file_path}: {e}")
        return None

def import_users():
    """Importuje użytkowników z pliku JSON do bazy danych"""
    print(f"Importowanie użytkowników z {USERS_JSON_PATH}...")
    
    try:
        data = load_json_data(USERS_JSON_PATH)
        if not data or 'users' not in data:
            print("Brak danych użytkowników do importu lub nieprawidłowy format.")
            return 0
        
        users_data = data['users']
        print(f"Znaleziono {len(users_data)} użytkowników w pliku JSON.")
        
        count = 0
        for user_data in users_data:
            if not isinstance(user_data, dict):
                print(f"Nieprawidłowy format danych użytkownika: {user_data}")
                continue
                
            # Sprawdź czy użytkownik już istnieje
            username = user_data.get('fullName') or user_data.get('username')
            email = user_data.get('email')
            
            if not username:
                print(f"Brak nazwy użytkownika w danych: {user_data}")
                continue
                
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"Użytkownik {username} już istnieje. Pomijam.")
                continue
            
            # Tworzenie nowego użytkownika
            new_user = User(
                username=username,
                email=email or f"{username.lower().replace(' ', '_')}@example.com",
                password_hash=user_data.get('password'),
                is_admin=username.lower() == "administrator"
            )
            db.session.add(new_user)
            print(f"Dodano użytkownika: {new_user.username}")
            count += 1
        
        if count > 0:
            db.session.commit()
            print(f"Zaimportowano {count} użytkowników.")
        
        return count
    except Exception as e:
        print(f"Błąd podczas importowania użytkowników: {e}")
        traceback.print_exc()
        return 0

def import_quizzes():
    """Importuje quizy z pliku JSON do bazy danych"""
    print(f"Importowanie quizów z {QUIZ_JSON_PATH}...")
    
    try:
        data = load_json_data(QUIZ_JSON_PATH)
        if not data or 'quizzes' not in data:
            print("Brak danych quizów do importu lub nieprawidłowy format.")
            return 0
        
        quizzes_data = data['quizzes']
        print(f"Znaleziono {len(quizzes_data)} quizów w pliku JSON.")
        
        count = 0
        for quiz_data in quizzes_data:
            if not isinstance(quiz_data, dict):
                print(f"Nieprawidłowy format danych quizu: {quiz_data}")
                continue
                
            title = quiz_data.get('title')
            if not title:
                print(f"Brak tytułu quizu w danych: {quiz_data}")
                continue
                
            # Sprawdź czy quiz już istnieje
            existing_quiz = Quiz.query.filter_by(title=title).first()
            if existing_quiz:
                print(f"Quiz '{title}' już istnieje. Pomijam.")
                continue
            
            # Znajdź użytkownika jeśli istnieje
            user_id = None
            if 'author' in quiz_data:
                user = User.query.filter_by(username=quiz_data['author']).first()
                if user:
                    user_id = user.id
            
            # Utwórz nowy quiz
            new_quiz = Quiz(
                title=title,
                description=quiz_data.get('description'),
                category=quiz_data.get('category'),
                difficulty=quiz_data.get('difficulty'),
                time_limit=quiz_data.get('timeLimit'),
                created_at=quiz_data.get('createdAt'),
                last_modified=quiz_data.get('lastModified'),
                user_id=user_id
            )
            
            # Ustaw pytania
            new_quiz.questions = quiz_data.get('questions', [])
            
            db.session.add(new_quiz)
            print(f"Dodano quiz: {new_quiz.title}")
            count += 1
        
        if count > 0:
            db.session.commit()
            print(f"Zaimportowano {count} quizów.")
        
        return count
    except Exception as e:
        print(f"Błąd podczas importowania quizów: {e}")
        traceback.print_exc()
        return 0

def init_and_import():
    """Inicjalizuje bazę danych i importuje dane"""
    print("=" * 50)
    print("Inicjalizacja bazy danych SQLite i import danych")
    print("=" * 50)
    
    try:
        # Tworzenie tabel
        print("\nTworzenie tabel w bazie danych...")
        with app.app_context():
            db.create_all()
            print("Tabele utworzone pomyślnie!")
          # Import danych
        print("\nRozpoczynam import danych...")
        with app.app_context():
            user_count = import_users()
            quiz_count = import_quizzes()
        
        print("\nPodsumowanie:")
        print(f"Zaimportowano {user_count} użytkowników")
        print(f"Zaimportowano {quiz_count} quizów")
        print("Proces zakończony pomyślnie!")
        
        return True
    except Exception as e:
        print(f"\nBŁĄD: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    init_and_import()
