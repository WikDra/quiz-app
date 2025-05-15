"""
Definicje tras API dla Quiz App
"""
import sys
import os
from flask import jsonify, request, redirect
from flask_jwt_extended import create_access_token, create_refresh_token
from pathlib import Path

# Dodaj ścieżkę projektu
module_path = os.path.abspath(os.path.dirname(__file__))
if module_path not in sys.path:
    sys.path.insert(0, module_path)

from controllers import QuizController, UserController
from controllers.oauth_controller import OAuthController
from models.user import User

def register_routes(app):
    """Rejestruje trasy API w aplikacji Flask"""
    
    # Dodaj logger
    import logging
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
      # Endpoint do sprawdzania stanu aplikacji
    @app.route('/api/health')
    def health_check():
        """Endpoint do sprawdzania stanu aplikacji"""
        return jsonify({'status': 'ok', 'message': 'Server is running'})
    
    # Endpointy dla użytkowników
    @app.route('/api/users')
    def get_users():
        """Zwraca listę użytkowników"""
        users, error = UserController.get_all_users()
        if error:
            return jsonify({'error': error}), 500
        return jsonify({"users": users})
        
    @app.route('/api/users/<int:user_id>', methods=['GET'])
    def get_user_by_id(user_id):
        """Zwraca dane pojedynczego użytkownika po ID"""
        app.logger.info(f"Pobieranie danych użytkownika o ID: {user_id}")
        user = User.query.get(user_id)
        if not user:
            app.logger.warning(f"Użytkownik o ID {user_id} nie został znaleziony")
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict()), 200
        
    @app.route('/api/users', methods=['PUT'])
    def update_users():
        """Aktualizuje listę użytkowników"""
        data = request.get_json()
        if not data or 'users' not in data:
            return jsonify({'error': 'No user data provided'}), 400
        
        result, error = UserController.update_users(data['users'])
        if error:
            return jsonify({'error': error}), 500
        return jsonify(result)
        
    @app.route('/api/users/<int:user_id>/avatar', methods=['PUT'])
    def update_user_avatar(user_id):
        """Aktualizuje awatar użytkownika"""
        data = request.get_json()
        if not data or 'avatar_url' not in data:
            return jsonify({'error': 'No avatar URL provided'}), 400
        
        result, error = UserController.update_user_avatar(user_id, data['avatar_url'])
        if error:
            return jsonify({'error': error}), 500
        return jsonify(result)
        
    @app.route('/api/register', methods=['POST'])
    def register():
        """Endpoint do rejestracji nowych użytkowników"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user, error = UserController.register_user(data)
        if error:
            return jsonify({'error': error}), 409 if "already exists" in error else 400
        # Jeśli user to obiekt User, zamień na dict
        if hasattr(user, 'to_dict'):
            return jsonify(user.to_dict()), 201
        return jsonify(user), 201
        
    @app.route('/api/login', methods=['POST'])
    def login():
        """Endpoint do logowania użytkowników"""
        app.logger.info("Otrzymano żądanie logowania w routes.py")
        data = request.get_json()
        if not data:
            app.logger.warning("Brak danych w żądaniu logowania")
            return jsonify({'error': 'No data provided'}), 400
        
        user, error = UserController.login_user(data.get('email'), data.get('password'))
        if error:
            status_code = 401 if "Invalid email or password" in error else 400
            app.logger.warning(f"Nieudane logowanie: {error}, kod: {status_code}")
            return jsonify({'error': error}), status_code
            
        try:
            # Create JWT tokens
            app.logger.info(f"Tworzenie tokenów JWT dla użytkownika {user.id}")
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
            app.logger.info(f"Logowanie zakończone sukcesem dla użytkownika: {user.email}")
            return jsonify(user_data=user.to_dict(), access_token=access_token, refresh_token=refresh_token), 200
        except Exception as e:
            app.logger.error(f"Błąd podczas tworzenia tokenów JWT: {str(e)}")
            return jsonify({'error': 'Internal server error during authentication'}), 500

    @app.route('/api/users/<int:user_id>', methods=['PUT'])
    def update_user_data_route(user_id):
        """Endpoint do aktualizacji danych użytkownika (imię, email)"""
        app.logger.info(f"Attempting to update data for user_id: {user_id}") # Dodane logowanie
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Spodziewane pola: fullName, email
        user_data, error = UserController.update_user_data(user_id, data)
        if error:
            status_code = 404 if error == "User not found" else 400
            if "Email already in use" in error:
                status_code = 409 # Conflict
            return jsonify({'error': error}), status_code
        return jsonify(user_data)

    @app.route('/api/users/<int:user_id>/change-password', methods=['PUT'])
    def change_password_route(user_id):
        """Endpoint do zmiany hasła użytkownika"""
        data = request.get_json()
        if not data or 'currentPassword' not in data or 'newPassword' not in data:
            return jsonify({'error': 'Missing currentPassword or newPassword'}), 400
        
        result, error = UserController.change_password(
            user_id,
            data['currentPassword'],
            data['newPassword']
        )
        if error:
            status_code = 404 if error == "User not found" else 400
            if "Invalid current password" in error or "Password must be at least 6 characters long" in error:
                status_code = 400
            return jsonify({'error': error}), status_code
        return jsonify(result)

    # Endpointy dla quizów
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
        
        return jsonify({'quizzes': quizzes})
    
    @app.route('/api/quiz/<int:quiz_id>', methods=['GET'])
    def get_quiz(quiz_id):
        """Endpoint do pobierania pojedynczego quizu"""
        app.logger.info(f"Otrzymano żądanie o quiz ID: {quiz_id}")
        
        quiz, error = QuizController.get_quiz_by_id(quiz_id)
        
        if error:
            app.logger.error(f"Błąd przy pobieraniu quizu {quiz_id}: {error}")
            return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
        
        # Logowanie szczegółów quizu
        app.logger.info(f"Zwracam quiz ID {quiz_id}: {quiz['title']}, liczba pytań: {len(quiz['questions']) if 'questions' in quiz else 0}")
        
        # Sprawdź strukturę pytań
        for i, question in enumerate(quiz.get('questions', [])):
            if 'correctAnswer' not in question:
                app.logger.error(f"Pytanie {i} nie ma pola correctAnswer")
            elif not isinstance(question['correctAnswer'], int):
                app.logger.warning(f"Pytanie {i}: correctAnswer ({question['correctAnswer']}) nie jest liczbą całkowitą, typ: {type(question['correctAnswer'])}")
                # Konwersja do int na wszelki wypadek
                question['correctAnswer'] = int(question['correctAnswer'])
                
            if 'options' not in question:
                app.logger.error(f"Pytanie {i} nie ma pola options")
            elif not isinstance(question['options'], list):
                app.logger.error(f"Pytanie {i}: options nie jest listą")
                
            if 'question' not in question:
                app.logger.error(f"Pytanie {i} nie ma tekstu pytania")
        
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
    
    # Endpointy OAuth dla Google
    @app.route('/api/login/google')
    def login_with_google():
        """Inicjuje proces logowania przez Google"""
        return OAuthController.login_with_google()
        
    @app.route('/api/authorize/google')
    def authorize_google():
        """Obsługuje callback po autoryzacji Google"""
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        try:
            result = OAuthController.handle_google_callback()
            if result is None:
                app.logger.error("OAuth callback returned None instead of (user, error)")
                return redirect(f"{frontend_url}/login?error=Internal+server+error")
                
            user, error_message = result
            app.logger.info(f"Google callback result: User: {user is not None}, Error: {error_message}")
        
            if error_message:
                # Przekieruj do frontendu z błędem
                error_query = f"?error={error_message}"
                app.logger.error(f"Redirecting to frontend with error: {error_message}")
                return redirect(f"{frontend_url}/login{error_query}")
        
            # Utwórz tokeny JWT tak jak przy zwykłym logowaniu
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            app.logger.info(f"Created tokens for OAuth user {user.email}")
        
            # Przekieruj do frontendu z tokenem w parametrach URL
            token_query = f"?access_token={access_token}&refresh_token={refresh_token}"
            app.logger.info(f"Redirecting to frontend with tokens to: {frontend_url}/oauth-callback{token_query}")
            return redirect(f"{frontend_url}/oauth-callback{token_query}")
        except Exception as e:
            app.logger.exception(f"Error in Google OAuth callback handling: {str(e)}")
            return redirect(f"{frontend_url}/login?error=Internal+OAuth+Error")
