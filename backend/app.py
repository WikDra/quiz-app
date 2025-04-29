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
import hashlib  # Dodaję import biblioteki do hashowania haseł

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
        # Dodaj pole "users" aby format odpowiedzi był zgodny z oczekiwanym przez frontend
        return jsonify({"users": result})
    except Exception as e:
        app.logger.error(f"Error retrieving users: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

# Dodaję obsługę aktualizacji danych użytkowników
@app.route('/api/users', methods=['PUT'])
def update_users():
    """Aktualizuje listę użytkowników (używane przez frontend)"""
    try:
        data = request.get_json()
        if not data or 'users' not in data:
            return jsonify({'error': 'No user data provided'}), 400
        
        users_data = data['users']
        updated_count = 0
        new_count = 0
        
        for user_data in users_data:
            # Sprawdź czy użytkownik o danym id już istnieje
            user_id = user_data.get('id')
            if user_id:
                existing_user = User.query.get(user_id)
                if existing_user:
                    # Aktualizuj istniejącego użytkownika
                    existing_user.username = user_data.get('fullName', existing_user.username)
                    existing_user.email = user_data.get('email', existing_user.email)
                    if 'password' in user_data:
                        existing_user.password_hash = user_data['password']  # W produkcji hasło powinno być hashowane
                    existing_user.is_admin = user_data.get('isAdmin', existing_user.is_admin)
                    updated_count += 1
                    continue
            
            # Jeśli nie znaleziono użytkownika o danym id, sprawdź czy istnieje użytkownik o tym samym emailu
            email = user_data.get('email')
            if email:
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    # Aktualizuj istniejącego użytkownika
                    existing_user.username = user_data.get('fullName', existing_user.username)
                    if 'password' in user_data:
                        existing_user.password_hash = user_data['password']  # W produkcji hasło powinno być hashowane
                    existing_user.is_admin = user_data.get('isAdmin', existing_user.is_admin)
                    updated_count += 1
                    continue
            
            # Jeśli nie znaleziono użytkownika, stwórz nowego
            if 'fullName' in user_data and 'email' in user_data:
                new_user = User(
                    username=user_data['fullName'],
                    email=user_data['email'],
                    password_hash=user_data.get('password'),  # W produkcji hasło powinno być hashowane
                    is_admin=user_data.get('isAdmin', False)
                )
                db.session.add(new_user)
                new_count += 1
        
        if updated_count > 0 or new_count > 0:
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Users updated: {updated_count}, new users added: {new_count}'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating users: {str(e)}")
        return jsonify({'error': f'Failed to update users: {str(e)}'}), 500

# Dodaję endpoint do rejestracji użytkowników
@app.route('/api/register', methods=['POST'])
def register():
    """Endpoint do rejestracji nowych użytkowników"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Sprawdź wymagane pola
        required_fields = ['fullName', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Sprawdź, czy użytkownik o podanym adresie email już istnieje
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Tworzenie nowego użytkownika
        new_user = User(
            username=data['fullName'],
            email=data['email'],
            password_hash=data['password'],  # W produkcji hasło powinno być hashowane
            is_admin=False
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Zwróć dane nowego użytkownika bez hasła
        user_data = new_user.to_dict()
        
        return jsonify(user_data), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

# Dodaję endpoint do logowania
@app.route('/api/login', methods=['POST'])
def login():
    """Endpoint do logowania użytkowników"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Sprawdź wymagane pola
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Znajdź użytkownika po emailu
        user = User.query.filter_by(email=data['email']).first()
        
        # Sprawdź czy użytkownik istnieje i czy hasło jest poprawne
        if not user or user.password_hash != data['password']:  # W produkcji porównanie zahashowanych haseł
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Zwróć dane użytkownika bez hasła
        user_data = user.to_dict()
        
        return jsonify(user_data), 200
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

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
    
    # Opakowujemy quizy w obiekt z kluczem 'quizzes' dla kompatybilności z frontendem
    return jsonify({'quizzes': quizzes})

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
