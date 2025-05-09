"""
Główny plik aplikacji Flask z obsługą API dla quizów.
Zawiera również definicje modeli i konfigurację bazy danych.
"""
import os
import json
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
import hashlib  # Dodaję import biblioteki do hashowania haseł
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, JWTManager, get_jwt_identity # Added JWT imports

# Import db instance from backend package
from . import db
# Import models
from .models.user import User
from .models.quiz import Quiz
# Import controllers
from .controllers.quiz_controller import QuizController

# Konfiguracja aplikacji
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_key_for_quiz_app' # Fallback, should be overridden by JWT_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'quiz_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = "super-secret-jwt-key-change-this"  # Change this in production!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False # For testing, consider setting an expiration time
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = False # For testing, consider setting an expiration time


# Inicjalizacja rozszerzeń
migrate = Migrate(app, db) # Initialize Migrate with the imported db
CORS(app)
jwt = JWTManager(app) # Initialize JWTManager

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
                    if 'password' in user_data and user_data['password']: # Check if password is provided and not empty
                        existing_user.set_password(user_data['password']) # Use set_password
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
                    if 'password' in user_data and user_data['password']: # Check if password is provided and not empty
                        existing_user.set_password(user_data['password']) # Use set_password
                    existing_user.is_admin = user_data.get('isAdmin', existing_user.is_admin)
                    updated_count += 1
                    continue
            
            # Jeśli nie znaleziono użytkownika, stwórz nowego
            if 'fullName' in user_data and 'email' in user_data:
                new_user = User(
                    username=user_data['fullName'],
                    email=user_data['email'],
                    # password_hash=user_data.get('password'),  # Removed direct assignment
                    is_admin=user_data.get('isAdmin', False)
                )
                if user_data.get('password'): # Check if password is provided
                    new_user.set_password(user_data.get('password')) # Use set_password
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
            # password_hash=data['password'],  # Removed direct assignment
            is_admin=False
        )
        new_user.set_password(data['password']) # Use set_password
        
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
        if not user or not user.check_password(data['password']):  # Use check_password
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id) # Optional: if you want refresh token functionality
        
        # Zwróć dane użytkownika bez hasła
        user_data = user.to_dict()
        
        return jsonify(user_data=user_data, access_token=access_token, refresh_token=refresh_token), 200 # Return tokens
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
