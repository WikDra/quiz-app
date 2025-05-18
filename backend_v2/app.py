"""
Main application module for Quiz App
"""
import os
import logging
from datetime import timedelta
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

# Import models and controllers
from models import db
from controllers.oauth_controller import init_oauth

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load environment variables
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        app.logger.info(f"Loaded environment variables from {dotenv_path}")
    else:
        app.logger.warning("No .env file found. Using default security keys, which is NOT recommended for production.")
        app.logger.warning("Run python utils/setup_security.py to create secure keys.")
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'UNSAFE_DEV_KEY_PLEASE_RUN_SETUP_SECURITY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'quiz_app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # JWT configuration
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'UNSAFE_DEV_JWT_KEY_PLEASE_RUN_SETUP_SECURITY')
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    
    # Configure JWT cookies
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # Set to True in production
    app.config["JWT_COOKIE_SAMESITE"] = "None"  # Required for cross-site requests
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    bcrypt = Bcrypt(app)
    
    # Configure CORS
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    CORS(
        app,
        origins=[frontend_url], 
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Set-Cookie"], 
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    
    # Initialize OAuth
    init_oauth(app)
    
    # Custom after_request function to ensure cookies work correctly
    @app.after_request
    def set_cookie_attributes(response):
        """Ensure cookies have proper attributes for cross-site requests"""
        # Get all cookie headers
        cookie_headers = response.headers.getlist('Set-Cookie')
        new_cookie_headers = []
        
        # Process each cookie
        for header in cookie_headers:
            # Replace samesite=Lax with samesite=None
            if 'samesite=Lax' in header:
                header = header.replace('samesite=Lax', 'samesite=None')
            # Add samesite=None if not present
            elif 'samesite=' not in header:
                header = header + '; samesite=None'
            new_cookie_headers.append(header)
        
        # Clear original cookies and set the modified ones
        response.headers.pop('Set-Cookie', None)
        for header in new_cookie_headers:
            response.headers.add('Set-Cookie', header)
        
        return response
    
    # Register all routes
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        # Register routes
        import routes
        routes.register_routes(app)
    
    return app


# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
