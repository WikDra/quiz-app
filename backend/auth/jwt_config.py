"""
JWT configuration module
"""
import os
import logging
from datetime import timedelta
from flask import jsonify
from flask_jwt_extended import JWTManager
from models.user import InvalidToken

# Initialize JWT Manager
jwt = JWTManager()
logger = logging.getLogger('app')

def init_jwt(app):
    """Initialize JWT configuration"""    # JWT configuration      
      # Token settings
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']  # Use only cookies, no headers
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=2)  # Short expiry for testing
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
      # Cookie settings
    app.config['JWT_COOKIE_SECURE'] = False  # TEMPORARILY FOR HTTP LOCAL DEV
    app.config['JWT_COOKIE_SAMESITE'] = 'None'  # Required for cross-site access
    app.config['JWT_COOKIE_DOMAIN'] = None  # Allow cookies for same-origin or specified domain
    app.config['JWT_SESSION_COOKIE'] = False  # Make it a non-session cookie
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True  # Enable CSRF protection
    app.config['JWT_CSRF_IN_COOKIES'] = False  # CSRF value in JWT payload, not separate cookies
    app.config['JWT_ACCESS_CSRF_HEADER_NAME'] = 'X-CSRF-TOKEN'
    app.config['JWT_REFRESH_CSRF_HEADER_NAME'] = 'X-CSRF-TOKEN'
    app.config['JWT_ACCESS_CSRF_FIELD_NAME'] = 'csrf'  # Field name in JWT payload for access token
    app.config['JWT_REFRESH_CSRF_FIELD_NAME'] = 'csrf'  # Field name in JWT payload for refresh token
    app.config['JWT_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Security settings
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
    
    jwt.init_app(app)

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logger.warning(f"Expired token used: {jwt_payload}")
        return jsonify({
            "error": "Token has expired",
            "code": "token_expired"
        }), 401
        
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        logger.warning(f"Invalid token: {error_string}")
        return jsonify({
            "error": "Token is invalid",
            "code": "token_invalid",
            "details": error_string
        }), 401
        
    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        logger.warning(f"Missing token: {error_string}")
        return jsonify({
            "error": "Authentication required",
            "code": "token_missing",
            "details": error_string
        }), 401
        
    @jwt.needs_fresh_token_loader
    def fresh_token_loader_callback(jwt_header, jwt_payload):
        logger.warning(f"Fresh token required: {jwt_payload}")
        return jsonify({
            "error": "Fresh login required for this action",
            "code": "fresh_token_required"
        }), 401
        
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        logger.warning(f"Revoked token used: {jwt_payload}")
        return jsonify({
            "error": "Token has been revoked",
            "code": "token_revoked"
        }), 401
    
    # Token blacklist loader
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if JWT token is revoked"""
        jti = jwt_payload["jti"]
        return InvalidToken.is_token_revoked(jti)

    logger.info("JWT configuration initialized")