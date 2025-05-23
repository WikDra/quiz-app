"""
Main Flask application setup
"""
import os
import sys
import time
import logging
import threading
from datetime import timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from models import db
from utils.setup_security import update_env_file
from routes import register_routes
from controllers.oauth_controller import init_oauth
from auth.jwt_config import init_jwt
from utils.token_utils import cleanup_expired_tokens

def start_token_cleanup_task(app):
    """Start a background thread that periodically cleans up expired tokens"""
    def cleanup_task():
        with app.app_context():
            while True:
                try:
                    cleanup_expired_tokens()
                    time.sleep(3600)  # Sleep for 1 hour
                except Exception as e:
                    app.logger.error(f"Error in token cleanup task: {str(e)}")
                    time.sleep(300)  # On error, retry after 5 minutes
    
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    app.logger.info("Token cleanup task started")

def create_app():
    """Create and configure the Flask application"""
    # Load environment variables
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('app')
    logger.info(f'Loaded environment variables from {env_path}')
      # Create Flask app
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///quiz_app.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure Flask secret key
    if not os.environ.get('FLASK_SECRET_KEY'):
        logger.error("FLASK_SECRET_KEY not set in environment variables")
        update_env_file()
    app.secret_key = os.environ.get('FLASK_SECRET_KEY')
    
    # JWT configuration and initialization
    if not os.environ.get('JWT_SECRET_KEY'):
        logger.error("JWT_SECRET_KEY not set in environment variables")
        update_env_file()
    init_jwt(app)
    
    # Frontend URL for CORS
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    app.config['CORS_ORIGINS'] = frontend_url    # Initialize extensions
    db.init_app(app)
      # Configure CORS
    CORS(app,
        resources={
            r"/api/*": {
                "origins": [frontend_url],
                "allow_headers": ["Content-Type", "Authorization", "X-CSRF-TOKEN"],
                "expose_headers": ["X-CSRF-TOKEN"],
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "supports_credentials": True,
                "send_wildcard": False
            }
        })
        
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        if not response.headers.get('Access-Control-Allow-Origin'):
            response.headers['Access-Control-Allow-Origin'] = frontend_url
        if not response.headers.get('Access-Control-Allow-Credentials'):
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRF-TOKEN'
            response.headers['Access-Control-Max-Age'] = '3600'
        return response
    
    # Configure OAuth
    oauth = init_oauth(app)
    
    # Register routes
    register_routes(app)
    
    # Start token cleanup task
    if not app.debug:
        start_token_cleanup_task(app)
    
    return app


# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
