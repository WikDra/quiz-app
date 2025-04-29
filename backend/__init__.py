"""
Inicjalizacja aplikacji Flask
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

# Inicjalizacja obiektów rozszerzeń
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Tworzy i konfiguruje instancję aplikacji Flask"""
    # Inicjalizacja aplikacji
    app = Flask(__name__)
    
    # Konfiguracja
    app.config['SECRET_KEY'] = 'dev_key_for_quiz_app'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'quiz_app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicjalizacja rozszerzeń
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Konfiguracja logowania
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    with app.app_context():
        # Rejestracja tras API (zrób to w kontekście aplikacji)
        import routes
        routes.register_routes(app)
    
    return app
