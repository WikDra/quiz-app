"""
Definicje tras API dla Quiz App
"""
import sys
import os
from flask import jsonify, request
from pathlib import Path

# Dodaj ścieżkę projektu
module_path = os.path.dirname(os.path.abspath(__file__))
if module_path not in sys.path:
    sys.path.append(module_path)

from controllers import QuizController, UserController

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
        return jsonify(user), 201
    
    @app.route('/api/login', methods=['POST'])
    def login():
        """Endpoint do logowania użytkowników"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user, error = UserController.login_user(data.get('email'), data.get('password'))
        if error:
            return jsonify({'error': error}), 401 if "Invalid email or password" in error else 400
        return jsonify(user)

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
