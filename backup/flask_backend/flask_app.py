"""
Główny plik aplikacji Flask z obsługą API dla quizów.
Zawiera również definicje modeli i konfigurację bazy danych.
"""
import os
import sys
import json
from pathlib import Path
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

# Konfiguracja aplikacji
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_key_for_quiz_app'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'quiz_app.db')
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

# Kontroler dla quizów
class QuizController:
    @staticmethod
    def get_all_quizzes(category=None, difficulty=None, search=None):
        """Pobiera wszystkie quizy z opcjonalnym filtrowaniem"""
        query = Quiz.query
        
        # Filtrowanie po kategorii
        if category:
            query = query.filter(Quiz.category == category)
        
        # Filtrowanie po trudności
        if difficulty:
            query = query.filter(Quiz.difficulty == difficulty)
        
        # Filtrowanie po wyszukiwaniu
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Quiz.title.ilike(search_term)) | 
                (Quiz.description.ilike(search_term))
            )
        
        try:
            quizzes = query.all()
            return [quiz.to_dict() for quiz in quizzes], None
        except Exception as e:
            app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while retrieving quizzes"
    
    @staticmethod
    def get_quiz_by_id(quiz_id):
        """Pobiera quiz na podstawie ID"""
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return None, "Quiz not found"
            return quiz.to_dict(), None
        except Exception as e:
            app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while retrieving quiz"
    
    @staticmethod
    def create_quiz(data):
        """Tworzy nowy quiz"""
        try:
            new_quiz = Quiz(
                title=data.get('title', ''),
                description=data.get('description', ''),
                category=data.get('category'),
                difficulty=data.get('difficulty'),
                time_limit=data.get('timeLimit'),
                user_id=data.get('userId'),
                created_at=data.get('createdAt'),
                last_modified=data.get('lastModified')
            )
            
            new_quiz.questions = data.get('questions', [])
            
            db.session.add(new_quiz)
            db.session.commit()
            
            return new_quiz.to_dict(), None
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while creating quiz"
    
    @staticmethod
    def update_quiz(quiz_id, data):
        """Aktualizuje istniejący quiz"""
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return None, "Quiz not found"
            
            quiz.title = data.get('title', quiz.title)
            quiz.description = data.get('description', quiz.description)
            quiz.category = data.get('category', quiz.category)
            quiz.difficulty = data.get('difficulty', quiz.difficulty)
            quiz.time_limit = data.get('timeLimit', quiz.time_limit)
            quiz.last_modified = data.get('lastModified', quiz.last_modified)
            
            if 'questions' in data:
                quiz.questions = data.get('questions')
            
            db.session.commit()
            
            return quiz.to_dict(), None
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while updating quiz"
    
    @staticmethod
    def delete_quiz(quiz_id):
        """Usuwa quiz o podanym ID"""
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return False, "Quiz not found"
            
            db.session.delete(quiz)
            db.session.commit()
            
            return True, None
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error: {str(e)}")
            return False, "Database error occurred while deleting quiz"

# API Endpoints
@app.route('/api/health')
def health_check():
    """Endpoint do sprawdzania stanu aplikacji"""
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/api/users')
def get_users():
    """Zwraca listę użytkowników"""
    try:
        users = User.query.all()
        result = [user.to_dict() for user in users]
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error retrieving users: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

@app.route('/api/quiz', methods=['GET'])
def get_quizzes():
    """Endpoint do pobierania wszystkich quizów z opcjonalnym filtrowaniem"""
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    search = request.args.get('search')
    
    quizzes, error = QuizController.get_all_quizzes(
        category=category,
        difficulty=difficulty,
        search=search
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(quizzes)

@app.route('/api/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """Endpoint do pobierania pojedynczego quizu"""
    quiz, error = QuizController.get_quiz_by_id(quiz_id)
    
    if error:
        return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
    
    return jsonify(quiz)

@app.route('/api/quiz', methods=['POST'])
def create_quiz():
    """Endpoint do tworzenia nowego quizu"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    quiz, error = QuizController.create_quiz(data)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(quiz), 201

@app.route('/api/quiz/<int:quiz_id>', methods=['PUT'])
def update_quiz(quiz_id):
    """Endpoint do aktualizacji istniejącego quizu"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    quiz, error = QuizController.update_quiz(quiz_id, data)
    
    if error:
        return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
    
    return jsonify(quiz)

@app.route('/api/quiz/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    """Endpoint do usuwania quizu"""
    success, error = QuizController.delete_quiz(quiz_id)
    
    if error:
        return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
    
    return jsonify({'message': 'Quiz deleted successfully'})

# Inicjalizacja bazy danych
def init_db():
    """Inicjalizuje bazę danych i tworzy tabele"""
    with app.app_context():
        db.create_all()
        print("Tabele zostały utworzone pomyślnie!")

# Start aplikacji
if __name__ == '__main__':
    # Sprawdź czy baza danych istnieje, jeśli nie - utwórz tabele
    db_path = os.path.join(os.path.dirname(__file__), 'quiz_app.db')
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        print("Inicjalizacja bazy danych...")
        init_db()
    
    app.run(host='127.0.0.1', port=5000, debug=True)
