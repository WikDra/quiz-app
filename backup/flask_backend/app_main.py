"""
Główny plik aplikacji Flask z obsługą API dla quizów.
"""
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from pathlib import Path

# Konfiguracja aplikacji
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_quiz_app')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'quiz_app.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicjalizacja rozszerzeń
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

# Import modeli
from app.models.user import User
from app.models.quiz import Quiz

# Import i rejestracja Blueprint dla tras API
from app.views.quiz_routes import quiz_bp
app.register_blueprint(quiz_bp)

# Endpoint sprawdzania stanu API
@app.route('/api/health')
def health_check():
    """Endpoint do sprawdzania stanu aplikacji"""
    return jsonify({'status': 'ok', 'message': 'Server is running'})

# Endpoint dla użytkowników (tymczasowy, do zastąpienia pełnym API)
@app.route('/api/users')
def get_users():
    """Zwraca listę użytkowników"""
    users = User.query.all()
    result = []
    
    for user in users:
        result.append({
            'id': user.id,
            'fullName': user.username,
            'email': user.email,
            'level': 'Początkujący', # Domyślne wartości dla brakujących pól
            'stats': {
                'quizzes': 0,
                'bestTime': '0min',
                'correctAnswers': 0
            }
        })
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
