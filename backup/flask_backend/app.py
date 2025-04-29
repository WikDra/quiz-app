"""
Plik startowy aplikacji Flask do obsługi quizów.
Ten plik uruchamia serwer Flask.
"""
import os
import sys
from pathlib import Path

# Dodaj katalog główny projektu do ścieżki Pythona
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

# Importowanie modułów Flask
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from app.config import config

# Inicjalizacja rozszerzeń
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    """Tworzy i konfiguruje instancję aplikacji Flask"""
    flask_app = Flask(__name__)
    
    # Ładowanie konfiguracji
    flask_app.config.from_object(config[config_name])
    
    # Inicjalizacja CORS
    CORS(flask_app)
    
    # Inicjalizacja rozszerzeń z aplikacją
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    
    # Import i rejestracja blueprintów
    from app.views.quiz_routes import quiz_bp
    flask_app.register_blueprint(quiz_bp)
    
    @flask_app.route('/api/health')
    def health_check():
        """Endpoint do sprawdzania stanu aplikacji"""
        return jsonify({'status': 'ok', 'message': 'Server is running'})
    
    return flask_app

if __name__ == '__main__':
    print("Uruchamianie aplikacji Quiz App z Flask...")
    app_instance = create_app('development')
    app_instance.run(host='127.0.0.1', port=5000, debug=True)
