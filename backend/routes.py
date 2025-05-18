"""
Definicje tras API dla Quiz App
"""
import sys
import os
from flask import jsonify, request, redirect, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from pathlib import Path

# Dodaj ścieżkę projektu
module_path = os.path.abspath(os.path.dirname(__file__))
if module_path not in sys.path:
    sys.path.insert(0, module_path)

from controllers import QuizController, UserController
from controllers.oauth_controller import OAuthController
from models.user import User
from utils.helpers import admin_required, sanitize_input

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
    @jwt_required()
    @admin_required
    def update_users():
        """Aktualizuje listę użytkowników (tylko dla administratorów)"""
        data = request.get_json()
        if not data or 'users' not in data:
            return jsonify({'error': 'No user data provided'}), 400
        
        # Sanityzacja danych wejściowych
        sanitized_users = []
        for user_data in data['users']:
            sanitized_user = {}
            for key, value in user_data.items():
                if key in ['fullName', 'email', 'id', 'isAdmin']:
                    sanitized_user[key] = sanitize_input(value) if isinstance(value, str) else value
            sanitized_users.append(sanitized_user)
            
        result, error = UserController.update_users(sanitized_users)
        if error:
            return jsonify({'error': error}), 500
        return jsonify(result)
        
    @app.route('/api/users/<int:user_id>/avatar', methods=['PUT'])
    @jwt_required()
    def update_user_avatar(user_id):
        """Aktualizuje awatar użytkownika"""
        # Sprawdź czy zalogowany użytkownik ma prawo modyfikować te dane
        current_user_id = get_jwt_identity()
        if int(current_user_id) != int(user_id):
            app.logger.warning(f"Unauthorized attempt to update avatar: user {current_user_id} tried to modify user {user_id}")
            return jsonify({'error': 'You do not have permission to update this user'}), 403
            
        data = request.get_json()
        if not data or 'avatar_url' not in data:
            return jsonify({'error': 'No avatar URL provided'}), 400
        
        # Sanityzacja danych wejściowych
        avatar_url = sanitize_input(data['avatar_url'])
        if not avatar_url:
            return jsonify({'error': 'Invalid avatar URL'}), 400
        
        result, error = UserController.update_user_avatar(user_id, avatar_url)
        if error:
            return jsonify({'error': error}), 500
        return jsonify(result)
    @app.route('/api/register', methods=['POST'])
    def register():
        """Endpoint do rejestracji nowych użytkowników"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Sanityzacja danych wejściowych przejmuje UserController.register_user
        user, error = UserController.register_user(data)
        if error:
            return jsonify({'error': error}), 409 if "already exists" in error else 400
            
        try:
            # Create JWT tokens
            app.logger.info(f"Tworzenie tokenów JWT dla nowego użytkownika {user.id}")
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)

            # Create response            user_data = user.to_dict() if hasattr(user, 'to_dict') else user
            resp = make_response(jsonify(user_data))

            # Set access token as HTTP-only cookie
            resp.set_cookie('access_token_cookie', access_token, httponly=True, secure=False, samesite='Lax')
            # Set refresh token as HTTP-only cookie
            resp.set_cookie('refresh_token_cookie', refresh_token, httponly=True, secure=False, samesite='Lax')
            
            return resp, 201
        except Exception as e:
            app.logger.error(f"Błąd podczas tworzenia tokenów JWT: {str(e)}")
            # Return user data without tokens if there's an error
            user_data = user.to_dict() if hasattr(user, 'to_dict') else user
            return jsonify(user_data), 201
    @app.route('/api/login', methods=['POST'])
    def login():
        """Endpoint do logowania użytkowników"""
        app.logger.info("Otrzymano żądanie logowania w routes.py")
        data = request.get_json()
        if not data:
            app.logger.warning("Brak danych w żądaniu logowania")
            return jsonify({'error': 'No data provided'}), 400
        
        # Sanityzacja danych wejściowych odbywa się w UserController.login_user
        user, error = UserController.login_user(data.get('email'), data.get('password'))
        if error:
            status_code = 401 if "Invalid email or password" in error else 400
            app.logger.warning(f"Nieudane logowanie: {error}, kod: {status_code}")
            return jsonify({'error': error}), status_code
            
        try:
            # Create JWT tokens
            app.logger.info(f"Tworzenie tokenów JWT dla użytkownika {user.id}")
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)            # Create response
            resp = jsonify(user_data=user.to_dict())

            # Set access token as HTTP-only cookie
            resp.set_cookie('access_token_cookie', access_token, httponly=True, secure=False, samesite='Lax')
            # Set refresh token as HTTP-only cookie
            resp.set_cookie('refresh_token_cookie', refresh_token, httponly=True, secure=False, samesite='Lax')
            
            app.logger.info(f"Logowanie zakończone sukcesem dla użytkownika: {user.email}")
            return resp, 200
        except Exception as e:
            app.logger.error(f"Błąd podczas tworzenia tokenów JWT: {str(e)}")
            return jsonify({'error': 'Internal server error during authentication'}), 500

    @app.route('/api/users/<int:user_id>', methods=['PUT'])
    @jwt_required()
    def update_user_data_route(user_id):
        """Endpoint do aktualizacji danych użytkownika (imię, email)"""
        # Sprawdź czy zalogowany użytkownik ma prawo modyfikować te dane
        current_user_id = get_jwt_identity()
        if int(current_user_id) != int(user_id):
            app.logger.warning(f"Unauthorized attempt to update user data: user {current_user_id} tried to modify user {user_id}")
            return jsonify({'error': 'You do not have permission to update this user'}), 403
            
        app.logger.info(f"Attempting to update data for user_id: {user_id}")
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Sanityzacja danych odbywa się w UserController.update_user_data
        user_data, error = UserController.update_user_data(user_id, data)
        if error:
            status_code = 404 if error == "User not found" else 400
            if "Email already in use" in error:
                status_code = 409 # Conflict
            return jsonify({'error': error}), status_code
        return jsonify(user_data)

    @app.route('/api/users/<int:user_id>/change-password', methods=['PUT'])
    @jwt_required()
    def change_password_route(user_id):
        """Endpoint do zmiany hasła użytkownika"""
        # Sprawdź czy zalogowany użytkownik ma prawo modyfikować hasło
        current_user_id = get_jwt_identity()
        if int(current_user_id) != int(user_id):
            app.logger.warning(f"Unauthorized attempt to change password: user {current_user_id} tried to modify user {user_id}")
            return jsonify({'error': 'You do not have permission to change this user\'s password'}), 403
            
        data = request.get_json()
        if not data or 'currentPassword' not in data or 'newPassword' not in data:
            return jsonify({'error': 'Missing currentPassword or newPassword'}), 400
        
        # Sanityzacja nie jest potrzebna dla haseł
        result, error = UserController.change_password(
            user_id,
            data['currentPassword'],
            data['newPassword']
        )
        if error:
            status_code = 404 if error == "User not found" else 400
            if "Invalid current password" in error or "Password must be at least" in error:
                status_code = 400
            return jsonify({'error': error}), status_code
        return jsonify(result)

    @app.route('/api/users/me/profile', methods=['GET'])
    @jwt_required()
    def get_my_profile():
        """Endpoint do pobierania profilu zalogowanego użytkownika."""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            app.logger.warning(f"Użytkownik o ID {current_user_id} nie został znaleziony")
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict()), 200

    # Endpointy dla quizów
    @app.route('/api/quiz', methods=['GET'])
    def get_quizzes():
        """Endpoint do pobierania wszystkich quizów z opcjonalnym filtrowaniem"""
        category = sanitize_input(request.args.get('category'))
        difficulty = sanitize_input(request.args.get('difficulty'))
        search = sanitize_input(request.args.get('search'))
        
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
    @jwt_required()
    def create_quiz():
        """Endpoint do tworzenia nowego quizu"""
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Dodaj id aktualnego użytkownika jako autora quizu
        current_user_id = get_jwt_identity()
        data['author_id'] = current_user_id
        
        # Sanityzacja danych wejściowych
        sanitized_data = {}
        for key, value in data.items():
            if key in ['title', 'category', 'difficulty', 'description', 'author_id']:
                sanitized_data[key] = sanitize_input(value) if isinstance(value, str) else value
            elif key == 'questions':
                sanitized_data[key] = []
                for q in value:
                    sanitized_q = {}
                    for qk, qv in q.items():
                        if qk in ['question', 'correctAnswer']:
                            sanitized_q[qk] = sanitize_input(qv) if isinstance(qv, str) else qv
                        elif qk == 'options' and isinstance(qv, list):
                            sanitized_q[qk] = [sanitize_input(opt) if isinstance(opt, str) else opt for opt in qv]
                        else:
                            sanitized_q[qk] = qv
                    sanitized_data[key].append(sanitized_q)
            else:
                sanitized_data[key] = value
        
        quiz, error = QuizController.create_quiz(sanitized_data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify(quiz), 201
    
    @app.route('/api/quiz/<int:quiz_id>', methods=['PUT'])
    @jwt_required()
    def update_quiz(quiz_id):
        """Endpoint do aktualizacji istniejącego quizu"""
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Sprawdź czy użytkownik jest autorem quizu lub adminem
        current_user_id = get_jwt_identity()
        quiz, _ = QuizController.get_quiz_by_id(quiz_id)
        if quiz:
            user = User.query.get(current_user_id)
            if not user.is_admin and ('author_id' not in quiz or quiz['author_id'] != current_user_id):
                app.logger.warning(f"User {current_user_id} attempted to update quiz {quiz_id} without permission")
                return jsonify({'error': 'You do not have permission to update this quiz'}), 403
        
        # Sanityzacja danych podobna jak w create_quiz
        sanitized_data = {}
        for key, value in data.items():
            if key in ['title', 'category', 'difficulty', 'description']:
                sanitized_data[key] = sanitize_input(value) if isinstance(value, str) else value
            elif key == 'questions':
                sanitized_data[key] = []
                for q in value:
                    sanitized_q = {}
                    for qk, qv in q.items():
                        if qk in ['question', 'correctAnswer']:
                            sanitized_q[qk] = sanitize_input(qv) if isinstance(qv, str) else qv
                        elif qk == 'options' and isinstance(qv, list):
                            sanitized_q[qk] = [sanitize_input(opt) if isinstance(opt, str) else opt for opt in qv]
                        else:
                            sanitized_q[qk] = qv
                    sanitized_data[key].append(sanitized_q)
            else:
                sanitized_data[key] = value
        
        quiz, error = QuizController.update_quiz(quiz_id, sanitized_data)
        if error:
            return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
        
        return jsonify(quiz)
    
    @app.route('/api/quiz/<int:quiz_id>', methods=['DELETE'])
    @jwt_required()
    def delete_quiz(quiz_id):
        """Endpoint do usuwania quizu"""
        # Sprawdź czy użytkownik jest autorem quizu lub adminem
        current_user_id = get_jwt_identity()
        quiz, _ = QuizController.get_quiz_by_id(quiz_id)
        if quiz:
            user = User.query.get(current_user_id)
            if not user.is_admin and ('author_id' not in quiz or quiz['author_id'] != current_user_id):
                app.logger.warning(f"User {current_user_id} attempted to delete quiz {quiz_id} without permission")
                return jsonify({'error': 'You do not have permission to delete this quiz'}), 403
        
        success, error = QuizController.delete_quiz(quiz_id)
        
        if error:
            return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
        return jsonify({'message': 'Quiz deleted successfully'})
    
    # Dodaj endpoint do odświeżania tokenów JWT    @app.route('/api/token/refresh', methods=['POST'])
    @jwt_required(refresh=True)
    def refresh_token():
        """Odświeża token dostępu przy użyciu refresh tokena"""
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
          # Create response
        resp = make_response(jsonify({'message': 'Token refreshed successfully'}))

        # Set new access token as HTTP-only cookie
        resp.set_cookie('access_token_cookie', access_token, httponly=True, secure=False, samesite='Lax')
        
        return resp, 200
    
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
            app.logger.info(f"Created tokens for OAuth user {user.email}")            # Create response with redirect
            resp = make_response(redirect(f"{frontend_url}/oauth-callback"))
            # Set access token as HTTP-only cookie
            resp.set_cookie('access_token_cookie', access_token, httponly=True, secure=False, samesite='None')
            # Set refresh token as HTTP-only cookie
            resp.set_cookie('refresh_token_cookie', refresh_token, httponly=True, secure=False, samesite='None')

            # Przekieruj do frontendu
            return resp
        except Exception as e:
            app.logger.exception(f"Error in Google OAuth callback handling: {str(e)}")
            return redirect(f"{frontend_url}/login?error=Internal+OAuth+Error")

    @app.route('/api/logout', methods=['POST'])
    def logout():
        """Endpoint to log out the user by clearing their cookies"""
        resp = make_response(jsonify({'message': 'Logged out successfully'}))
        resp.delete_cookie('access_token_cookie')
        resp.delete_cookie('refresh_token_cookie')
        return resp, 200
