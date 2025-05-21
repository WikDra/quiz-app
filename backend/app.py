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
import stripe # Add Stripe import

# Import models and controllers
from models import db
from controllers.oauth_controller import init_oauth

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
      # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,  # Set to DEBUG for development
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
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    
    # Additional JWT security settings
    app.config["JWT_COOKIE_DOMAIN"] = os.environ.get('COOKIE_DOMAIN', None)  # Set in production
    app.config["JWT_MAX_REFRESH_COUNT"] = 100  # Maximum number of times a token can be refreshed
    app.config["JWT_REFRESH_TOKEN_ROTATION"] = True  # Enable refresh token rotation
    app.config["JWT_BLACKLIST_ENABLED"] = True  # Enable token blacklisting for revoked tokens
    app.config["JWT_IDENTITY_CLAIM"] = "sub"  # Use 'sub' claim for user ID
    app.config["JWT_ERROR_MESSAGE_KEY"] = "error"  # Key for error messages in responses
    
    # JWT token claims customization
    app.config["JWT_DECODE_ALGORITHMS"] = ["HS256"]  # Allowed algorithms for token verification
    app.config["JWT_PRIVATE_CLAIMS_PREFIX"] = "quiz_"  # Prefix for custom claims
    
    # Stripe configuration
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    app.config['STRIPE_PUBLISHABLE_KEY'] = os.environ.get('STRIPE_PUBLISHABLE_KEY') # Though primarily for frontend, can be useful here
    app.config['STRIPE_WEBHOOK_SECRET'] = os.environ.get('STRIPE_WEBHOOK_SECRET')

    # Determine if we're in production for cookie security settings
    is_production = os.environ.get('FLASK_ENV') == 'production'
    app.config["JWT_COOKIE_SECURE"] = True  # Always secure for SameSite=None to work
    app.config["JWT_COOKIE_CSRF_PROTECT"] = is_production  # Enable in production
    app.config["JWT_COOKIE_SAMESITE"] = "None"  # Required for cross-site requests
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
      # JWT error handlers    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        token_type = jwt_payload.get('type', 'access')
        app.logger.warning(f"Expired {token_type} token used: {jwt_payload}")
        
        error_message = (
            "Refresh token has expired. Please log in again."
            if token_type == "refresh"
            else "Access token has expired. Please refresh your token."
        )
        
        return jsonify({
            "error": error_message,
            "code": "token_expired",
            "token_type": token_type
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        app.logger.warning(f"Invalid token or decode error: {error_string}")
        return jsonify({
            "error": "Invalid token format or signature",
            "code": "token_invalid",
            "details": error_string
        }), 401
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        app.logger.warning(f"Missing token: {error_string}")
        return jsonify({
            "error": "Authentication required",
            "code": "token_missing",
            "details": error_string
        }), 401
        
    @jwt.needs_fresh_token_loader
    def fresh_token_loader_callback(jwt_header, jwt_payload):
        app.logger.warning(f"Fresh token required: {jwt_payload}")
        return jsonify({
            "error": "Fresh login required for this action",
            "code": "fresh_token_required"
        }), 401
        
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        app.logger.warning(f"Revoked token used: {jwt_payload}")
        return jsonify({
            "error": "Token has been revoked",
            "code": "token_revoked"
        }), 401
        
    @jwt.token_verification_failed_loader
    def verification_failed_callback(jwt_header, jwt_payload):
        app.logger.warning(f"Token verification failed: {jwt_payload}")
        return jsonify({
            "error": "Token verification failed",
            "code": "token_verification_failed"
        }), 401
        
    bcrypt = Bcrypt(app)      # Configure CORS
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    CORS(
        app,
        origins=[frontend_url], 
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Set-Cookie"], 
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        max_age=3600  # Cache preflight requests for 1 hour
    )
      # Initialize OAuth
    init_oauth(app)
      # Custom after_request function to ensure cookies work correctly
    @app.after_request
    def set_cookie_attributes(response):
        """Ensure cookies have proper attributes for cross-site requests"""
        # Get all cookie headers
        cookie_headers = response.headers.getlist('Set-Cookie')
        if not cookie_headers:
            return response
            
        new_cookie_headers = []
        
        # Check if running in production (HTTPS)
        is_production = os.environ.get('FLASK_ENV') == 'production'
        
        # Process each cookie
        for header in cookie_headers:
            # Add necessary security attributes for cross-site requests
            if 'access_token_cookie' in header or 'refresh_token_cookie' in header:
                # Parse the cookie into parts
                parts = header.split(';')
                base = parts[0]  # The name=value part                
                attributes = {
                    'Path': '/',
                    'SameSite': 'None',  # Required for cross-site requests
                    'HttpOnly': True,    # Security: no JS access to cookie
                    'Secure': True       # Must be True for SameSite=None to work
                }
                
                # Keep any existing attributes that we're not explicitly setting
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.strip().split('=', 1)
                        if key.lower() not in [k.lower() for k in attributes.keys()]:
                            attributes[key] = value
                
                # Rebuild the cookie with our required attributes
                new_header = base
                for key, value in attributes.items():
                    if value is True:
                        new_header += f'; {key}'
                    else:
                        new_header += f'; {key}={value}'
                
                new_cookie_headers.append(new_header)
            else:
                # For non-JWT cookies, just pass them through
                new_cookie_headers.append(header)
          # Clear original cookies and set the modified ones
        response.headers.pop('Set-Cookie', None)
        for header in new_cookie_headers:
            response.headers.add('Set-Cookie', header)
              # Fix CORS headers - completely remove and reset credentials header
        # First, check if any of the Access-Control headers have multiple values
        for header_name in list(response.headers.keys()):
            if header_name.startswith('Access-Control'):
                # Get all values for this header
                values = response.headers.getlist(header_name)
                if len(values) > 1:
                    # If multiple values, remove all and re-add just one
                    app.logger.warning(f"Found duplicate CORS header: {header_name} with values: {values}")
                    response.headers.pop(header_name, None)
                    # Always use the first value
                    response.headers.add(header_name, values[0])
        
        # Make sure the credentials header is set correctly 
        # (needed after we merged from other endpoints that might've added it directly)
        if 'Access-Control-Allow-Credentials' in response.headers:
            # Only fix if it's not already set correctly
            if response.headers.get('Access-Control-Allow-Credentials') != 'true':
                response.headers.pop('Access-Control-Allow-Credentials', None)
                response.headers.add('Access-Control-Allow-Credentials', 'true')
        
        # Debug logging for CORS headers
        if app.debug:
            cors_headers = {k: v for k, v in response.headers.items() if k.startswith('Access-Control')}
            app.logger.debug(f"CORS headers after modification: {cors_headers}")
        
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
