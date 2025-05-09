"""
Główny plik aplikacji Flask z obsługą API dla quizów.
Zawiera również definicje modeli i konfigurację bazy danych.
"""
import os
import json
from datetime import timedelta # Added for token expiration
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
from .controllers.user_controller import UserController # Added UserController import

# Konfiguracja aplikacji
app = Flask(__name__)

# Load secret keys from environment variables with fallbacks for development
# IMPORTANT: For production, set these environment variables to strong, unique values.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_fallback')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev_jwt_secret_key_fallback') # Changed

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'quiz_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Configure token expiration times
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1) # Example: 1 hour
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30) # Example: 30 days


# Inicjalizacja rozszerzeń
migrate = Migrate(app, db) # Initialize Migrate with the imported db

# Configure CORS more restrictively for production
# FRONTEND_URL should be set as an environment variable in production
# For development, you might allow '*' or specific local origins.
frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173') # Default to common Vite dev port
CORS(app, resources={r"/api/*": {"origins": frontend_url}}) # Restrict to frontend URL

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
@jwt_required()  # Protect this route
def update_users():
    """Aktualizuje listę użytkowników (używane przez frontend). Tylko dla administratorów."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

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
                    # Usunięto możliwość zmiany hasła przez ten endpoint
                    # if 'password' in user_data and user_data['password']:
                    #     existing_user.set_password(user_data['password'])
                    if 'isAdmin' in user_data: # Allow admin to change isAdmin status
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
                    # Usunięto możliwość zmiany hasła przez ten endpoint
                    # if 'password' in user_data and user_data['password']:
                    #     existing_user.set_password(user_data['password'])
                    if 'isAdmin' in user_data: # Allow admin to change isAdmin status
                        existing_user.is_admin = user_data.get('isAdmin', existing_user.is_admin)
                    updated_count += 1
                    continue
            
            # Jeśli nie znaleziono użytkownika, stwórz nowego (admin operation)
            if 'fullName' in user_data and 'email' in user_data:
                new_user = User(
                    username=user_data['fullName'],
                    email=user_data['email'],
                    is_admin=user_data.get('isAdmin', False) # Admin can set isAdmin for new user
                )
                # Hasło dla nowego użytkownika powinno być ustawione w inny sposób,
                # np. generowane losowo i wysyłane do użytkownika, lub użytkownik sam je ustawia przy pierwszym logowaniu.
                # For now, new users created via this admin bulk endpoint won't have a password set here.
                # if user_data.get('password'):
                #     new_user.set_password(user_data.get('password'))
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
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Sprawdź wymagane pola - UserController can handle this
    # required_fields = ['fullName', 'email', 'password']
    # for field in required_fields:
    #     if field not in data or not data[field].strip():
    #         return jsonify({'error': f'Field {field} is required'}), 400

    user, error_message, status_code = UserController.register_user(data)

    if error_message:
        return jsonify({'error': error_message}), status_code
    
    return jsonify(user.to_dict()), 201


# Dodaję endpoint do logowania
@app.route('/api/login', methods=['POST'])
def login():
    """Endpoint do logowania użytkowników"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user, error_message, status_code = UserController.login_user(email, password)

    if error_message:
        return jsonify({'error': error_message}), status_code
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify(user_data=user.to_dict(), access_token=access_token, refresh_token=refresh_token), 200

@app.route('/api/users/me/profile', methods=['PUT'])
@jwt_required()
def update_my_profile():
    """Endpoint for the logged-in user to update their own profile (fullName, email)."""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Filter data to only allow specific fields to be updated by the user themselves
    allowed_updates = {
        'fullName': data.get('fullName'),
        'email': data.get('email')
    }
    # Remove None values if fields are not provided
    update_data = {k: v for k, v in allowed_updates.items() if v is not None}

    if not update_data:
        return jsonify({'error': 'No valid data provided for update'}), 400

    user, error_message, status_code = UserController.update_user_data(current_user_id, update_data)

    if error_message:
        return jsonify({'error': error_message}), status_code
    
    return jsonify(user.to_dict()), 200

@app.route('/api/users/me/password', methods=['PUT'])
@jwt_required()
def change_my_password():
    """Endpoint for the logged-in user to change their password."""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password are required'}), 400

    success, error_message, status_code = UserController.change_password(current_user_id, current_password, new_password)

    if error_message:
        return jsonify({'error': error_message}), status_code
    
    return jsonify({'message': 'Password updated successfully'}), 200

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
@jwt_required()  # Protect this route
def create_quiz():
    """Endpoint do tworzenia nowego quizu"""
    current_user_id = get_jwt_identity() # Get user ID from JWT
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Ensure the quiz is created for the currently logged-in user
    data['userId'] = current_user_id 
    
    quiz, error = QuizController.create_quiz(data)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(quiz), 201

@app.route('/api/quiz/<int:quiz_id>', methods=['PUT'])
@jwt_required()  # Protect this route
def update_quiz(quiz_id):
    """Endpoint do aktualizacji istniejącego quizu"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    quiz_to_update, error = QuizController.get_quiz_by_id(quiz_id) # We need the quiz object first to check ownership

    if error:
        return jsonify({'error': error}), 404 if error == "Quiz not found" else 400

    if not quiz_to_update:
        return jsonify({'error': 'Quiz not found'}), 404

    # Check if the current user is the author of the quiz or an admin
    # The quiz_to_update is a dict here, so we access userId via key
    if quiz_to_update.get('userId') != current_user_id and (not current_user or not current_user.is_admin):
        return jsonify({'error': 'Forbidden: You are not the author of this quiz or not an admin.'}), 403

    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Prevent changing the userId during update, unless by an admin for specific reasons (not implemented here)
    if 'userId' in data and data['userId'] != quiz_to_update.get('userId') and (not current_user or not current_user.is_admin):
        return jsonify({'error': 'Forbidden: You cannot change the author of the quiz.'}), 403
    elif 'userId' in data and data['userId'] != quiz_to_update.get('userId') and current_user and current_user.is_admin:
        # Admin is allowed to change userId, proceed with caution or add specific logic if needed
        pass # Explicitly allow admin to change userId if necessary, though generally not recommended via generic update
    elif 'userId' in data and data['userId'] == quiz_to_update.get('userId'):
        # If userId is in data but it's the same, it's fine
        pass
    else:
        # If userId is not in data, ensure it's not accidentally removed or changed by QuizController
        # Best practice: QuizController.update_quiz should handle this, or we ensure data sent to it is correct.
        # For now, we assume QuizController.update_quiz doesn't change userId unless explicitly in data.
        pass 

    quiz, error = QuizController.update_quiz(quiz_id, data)
    
    if error:
        return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
    
    return jsonify(quiz)

@app.route('/api/quiz/<int:quiz_id>', methods=['DELETE'])
@jwt_required()  # Protect this route
def delete_quiz(quiz_id):
    """Endpoint do usuwania quizu"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    quiz_to_delete, error = QuizController.get_quiz_by_id(quiz_id) # We need the quiz object first to check ownership

    if error: # This error is from get_quiz_by_id
        return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
    
    if not quiz_to_delete: # Should be caught by the error above, but as a safeguard
        return jsonify({'error': 'Quiz not found'}), 404

    # Check if the current user is the author of the quiz or an admin
    # The quiz_to_delete is a dict here, so we access userId via key
    if quiz_to_delete.get('userId') != current_user_id and (not current_user or not current_user.is_admin):
        return jsonify({'error': 'Forbidden: You are not the author of this quiz or not an admin.'}), 403

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
    
    # For production, use a WSGI server like Gunicorn or uWSGI instead of app.run()
    # and ensure debug is set to False.
    app.run(host='127.0.0.1', port=5000, debug=True) # debug=True is suitable for development
