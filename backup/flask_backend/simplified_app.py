"""
Uproszczony skrypt do uruchomienia aplikacji Flask z bazą SQLite
"""
import os
import sys
from pathlib import Path

# Dodaj katalog główny projektu do ścieżki Pythona
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate

# Tworzenie instancji Flask i rozszerzeń
app = Flask(__name__)

# Konfiguracja aplikacji
app.config['SECRET_KEY'] = 'dev_key_for_quiz_app'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(BASE_DIR / 'quiz_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicjalizacja rozszerzeń
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

# Import modeli po inicjalizacji db
from app.models.user import User
from app.models.quiz import Quiz

# Rejestracja blueprintów
from app.views.quiz_routes import quiz_bp
app.register_blueprint(quiz_bp)

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

# Funkcja do inicjalizacji bazy danych
def init_db():
    with app.app_context():
        db.create_all()
        print("Tabele zostały utworzone pomyślnie!")

if __name__ == '__main__':
    print("Uruchamianie aplikacji Quiz App z Flask...")
    app.run(host='127.0.0.1', port=5000, debug=True)
