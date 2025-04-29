"""
Moduł z funkcją tworzącą aplikację Flask
"""
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    """
    Tworzy i konfiguruje instancję aplikacji Flask
    """
    app = Flask(__name__)
    
    # Import config po utworzeniu aplikacji, aby uniknąć cyklicznych importów
    from app.config import config
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize CORS
    CORS(app)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import blueprints inside the function to avoid circular imports
    from app.views.quiz_routes import quiz_bp
    app.register_blueprint(quiz_bp)
    
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'ok', 'message': 'Server is running'})
    
    return app
