"""
Modified app.py with CORS fixes for cookie authentication.
Replace your existing app.py with this file to fix the CORS issues.
"""
import os
from datetime import timedelta # Added for token expiration
from flask import Flask, jsonify, request, redirect, make_response, after_this_request
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, JWTManager, get_jwt_identity # Added JWT imports
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import zmiennych środowiskowych
from dotenv import load_dotenv

# Szukaj pliku .env w głównym katalogu backend
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

# Jeśli plik .env istnieje, załaduj go
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Załadowano zmienne środowiskowe z {dotenv_path}")
else:
    print("Nie znaleziono pliku .env. Używanie domyślnych kluczy bezpieczeństwa, co NIE jest zalecane.")
    print("Uruchom python utils/setup_security.py, aby utworzyć bezpieczne klucze.")

# Import db instance from backend package
from . import db
# Import models
from .models.user import User
from .models.quiz import Quiz
# Import controllers
from .controllers.quiz_controller import QuizController
from .controllers.user_controller import UserController # Added UserController import
from .controllers.oauth_controller import OAuthController, init_oauth # Added OAuth controller import

# Konfiguracja aplikacji
app = Flask(__name__)

# Configure rate limiting
limiter = Limiter(
    get_remote_address, # Use get_remote_address to identify clients by IP
    app=app,
    default_limits=["200 per day", "50 per hour"], # Default limits for all routes
    storage_uri="memory://",  # For production, consider a persistent storage like Redis (e.g., "redis://localhost:6379")
    strategy="fixed-window" # Strategy for rate limiting (other option: "moving-window")
)

# Load secret keys from environment variables with fallbacks for development
# IMPORTANT: For production, set these environment variables to strong, unique values.
# Use utils/setup_security.py to generate secure keys and update the .env file
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'UNSAFE_DEV_KEY_PLEASE_RUN_SETUP_SECURITY')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'UNSAFE_DEV_JWT_KEY_PLEASE_RUN_SETUP_SECURITY')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'quiz_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Configure token expiration times
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1) # Example: 1 hour
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30) # Example: 30 days

# JWT cookie configuration
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False  # Set to False for development, True in production
app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # For development only, should be True in production
app.config["JWT_COOKIE_SAMESITE"] = "None"  # Use None for cross-site requests

# Configure JWT cookie names
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token_cookie"
app.config["JWT_REFRESH_COOKIE_NAME"] = "refresh_token_cookie"

# Inicjalizacja rozszerzeń
migrate = Migrate(app, db) # Initialize Migrate with the imported db

# Configure CORS more restrictively for production
# FRONTEND_URL should be set as an environment variable in production
# For development, you might allow '*' or specific local origins.
frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173') # Default to common Vite dev port

# Use a simpler CORS setup for now
CORS(app, origins=[frontend_url], 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Set-Cookie"], 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# JWTManager jest już zainicjalizowany w __init__.py

# Initialize OAuth
init_oauth(app)

# Import routes and register them with app
from .routes import register_routes
register_routes(app)

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
