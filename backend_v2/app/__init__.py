from flask import Flask, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
import os
from datetime import timedelta

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
oauth = OAuth()
oauth_initialized = False

def init_oauth(app):
    global oauth, oauth_initialized
    if oauth_initialized:
        app.logger.info("OAuth already initialized, skipping...")
        return oauth

    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    oauth_initialized = True
    app.logger.info("OAuth initialized successfully with Google provider")
    return oauth

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Load configuration
    from config.settings import config
    app.config.from_object(config[config_name])
      # CSRF protection setup
    def handle_csrf_error(e):
        # Get CSRF token from headers or JSON body
        token = request.headers.get('X-CSRFToken') or \
                (request.get_json(silent=True) or {}).get('csrf_token')
        
        app.logger.error(f'CSRF Error: {str(e)}')
        app.logger.debug(f'CSRF Debug - Request headers: {dict(request.headers)}')
        app.logger.debug(f'CSRF Debug - Request JSON: {request.get_json(silent=True)}')
        app.logger.debug(f'CSRF Debug - CSRF Token found: {token is not None}')
        app.logger.debug(f'CSRF Debug - Session: {dict(session)}')
        
        return jsonify({
            'success': False,
            'message': f'CSRF validation failed: {str(e)}'
        }), 400

    # Additional CSRF configuration
    app.config.update(
        WTF_CSRF_TIME_LIMIT=None,  # No time limit for CSRF tokens
        WTF_CSRF_CHECK_DEFAULT=True,  # Enable CSRF protection by default
        WTF_CSRF_SSL_STRICT=False,  # Don't require HTTPS for CSRF (dev only)
        WTF_CSRF_HEADERS=['X-CSRFToken'],  # Only check this header name
        WTF_CSRF_FIELD_NAME='csrf_token'  # Field name in JSON/form data
    )

    csrf.init_app(app)
    app.register_error_handler(CSRFError, handle_csrf_error)

    # Session configuration
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # Should be True in production
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_NAME='session',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        REMEMBER_COOKIE_SECURE=False,  # Should be True in production
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_DURATION=timedelta(days=7)
    )
    
    # Configure CORS
    cors_origins = app.config.get('CORS_ORIGINS', [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5174'
    ])
    if isinstance(cors_origins, str):
        cors_origins = cors_origins.split(',')
    
    CORS(app, 
         resources={r"/api/*": {
             "origins": cors_origins,
             "supports_credentials": True,
             "allow_headers": ["Content-Type", "X-CSRF-Token", "X-CSRFToken", "Authorization"],
             "expose_headers": ["X-CSRF-Token", "X-CSRFToken"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
         }})
      # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    limiter.init_app(app)
    init_oauth(app)
    
    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Musisz się zalogować aby uzyskać dostęp do tej strony.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
    login_manager.remember_cookie_duration = timedelta(days=7)
    
    @login_manager.user_loader
    def load_user(user_id):
        if not user_id:
            return None
        try:
            from app.models.user import User
            return User.query.get(int(user_id))
        except (ValueError, TypeError) as e:
            app.logger.error(f"Error loading user: {e}")
            return None
        except Exception as e:
            app.logger.error(f"Unexpected error loading user: {e}")
            return None
    
    # Register blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.quiz_controller import quiz_bp
    from app.controllers.user_controller import user_bp
    from app.controllers.stripe_controller import stripe_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(stripe_bp, url_prefix='/api/stripe')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'ok', 'message': 'Backend v2 działa prawidłowo'}
    
    return app
