"""
Inicjalizacja aplikacji Flask
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from datetime import timedelta

# Inicjalizacja obiektów rozszerzeń
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    """Tworzy i konfiguruje instancję aplikacji Flask"""
    # Inicjalizacja aplikacji
    app = Flask(__name__)
    
    # Konfiguracja
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_quiz_app')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'quiz_app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Konfiguracja JWT
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev_jwt_secret_key_fallback')
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    
    # Inicjalizacja rozszerzeń
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Konfiguracja logowania
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Załaduj zmienne środowiskowe (np. GOOGLE_CLIENT_ID/SECRET) przed inicjalizacją OAuth
    from dotenv import load_dotenv
    load_dotenv()
    # Inicjalizacja OAuth ( Google )
    # Initialize Google OAuth
    from controllers.oauth_controller import init_oauth
    init_oauth(app)

    with app.app_context():
        # Rejestracja tras API (zrób to w kontekście aplikacji)
        import routes
        routes.register_routes(app)
    
    return app
