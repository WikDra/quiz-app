# Authentication Route Cleanup

This document outlines a better organization for the authentication routes in the backend. Currently, the `routes.py` file is too large and contains many endpoints mixed together.

## Current issues:

1. The `/api/test-auth-cookies` endpoint still has issues with CORS headers
2. Too many debug endpoints scattered throughout the codebase
3. Duplicate code for setting cookies and handling authentication

## Recommendation:

Split the routes.py file into the following modules:

### 1. auth_routes.py
```python
"""Authentication routes for the Quiz App"""
from flask import jsonify, request, redirect, make_response
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jwt_identity, 
    jwt_required, verify_jwt_in_request
)
from controllers.oauth_controller import OAuthController
from controllers.user_controller import UserController
from models.user import User

def register_auth_routes(app):
    """Register authentication routes"""
    
    @app.route('/api/login', methods=['POST'])
    def login():
        """Login user with email and password"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user, error = UserController.login_user(data.get('email'), data.get('password'))
        if error:
            return jsonify({'error': error}), 401
            
        # Create JWT tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # Create response
        resp = jsonify(user_data=user.to_dict())
        
        # Set cookies with common helper
        set_auth_cookies(resp, access_token, refresh_token)
        
        return resp, 200

    @app.route('/api/register', methods=['POST'])
    def register():
        """Register new user"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user, error = UserController.register_user(data)
        if error:
            return jsonify({'error': error}), 409 if "already exists" in error else 400
            
        # Create JWT tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # Create response
        resp = make_response(jsonify(user.to_dict()))
        
        # Set cookies with common helper
        set_auth_cookies(resp, access_token, refresh_token)
        
        return resp, 201
    
    @app.route('/api/token/refresh', methods=['POST'])
    @jwt_required(refresh=True)    
    def refresh_token():
        """Refresh access token using refresh token"""
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=str(current_user_id))
        
        resp = make_response(jsonify({'message': 'Token refreshed successfully'}))
        resp.set_cookie(
            'access_token_cookie', 
            access_token, 
            httponly=True, 
            secure=False,  # Set to True in production with HTTPS
            samesite='None',  # Required for cross-site requests
            path='/'
        )
        
        return resp, 200
    
    @app.route('/api/logout', methods=['POST'])
    def logout():
        """Logout user by clearing cookies"""
        resp = make_response(jsonify({'message': 'Logged out successfully'}))
        resp.delete_cookie('access_token_cookie', path='/')
        resp.delete_cookie('refresh_token_cookie', path='/')
        resp.delete_cookie('auth_success', path='/')
        return resp, 200
    
    @app.route('/api/login/google')
    def login_with_google():
        """Initiate Google OAuth login process"""
        return OAuthController.login_with_google()
    
    @app.route('/api/authorize/google')
    def authorize_google():
        """Handle callback after Google authorization"""
        frontend_url = app.config.get('FRONTEND_URL', 'http://localhost:5173')
        
        try:
            result = OAuthController.handle_google_callback()
            if result is None or result[0] is None:
                app.logger.error("OAuth callback error")
                return redirect(f"{frontend_url}/login?error=OAuth+Error")
                
            user, error_message = result
            
            if error_message:
                return redirect(f"{frontend_url}/login?error={error_message}")
            
            # Create JWT tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            # Create response with redirect
            resp = make_response(redirect(f"{frontend_url}/oauth-callback"))
            
            # Set cookies with common helper
            set_auth_cookies(resp, access_token, refresh_token)
            
            return resp
            
        except Exception as e:
            app.logger.exception(f"Error in OAuth callback: {str(e)}")
            return redirect(f"{frontend_url}/login?error=Internal+Error")

def set_auth_cookies(response, access_token, refresh_token):
    """Helper to set authentication cookies consistently"""
    # Set access token cookie
    response.set_cookie(
        'access_token_cookie', 
        access_token, 
        httponly=True, 
        path='/',
        secure=False,  # Set to True in production with HTTPS
        samesite='None'  # Required for cross-site requests
    )
    
    # Set refresh token cookie
    response.set_cookie(
        'refresh_token_cookie', 
        refresh_token, 
        httponly=True, 
        path='/',
        secure=False,  # Set to True in production with HTTPS
        samesite='None'  # Required for cross-site requests
    )
    
    # Add a visible cookie for frontend detection
    response.set_cookie(
        'auth_success', 
        'true', 
        httponly=False, 
        path='/',
        secure=False,
        samesite='None',
        max_age=3600  # Set to expire in 1 hour
    )
```

### 2. debug_routes.py
```python
"""Debug routes for the Quiz App - NOT FOR PRODUCTION"""
import os
from datetime import datetime
from flask import jsonify, request, make_response
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

def register_debug_routes(app):
    """Register debugging routes (only for development)"""
    
    # Skip registration in production
    if app.config.get('ENV') == 'production':
        return
    
    @app.route('/api/debug/auth', methods=['GET'])
    def debug_auth():
        """Debug endpoint to check authentication status and cookies"""
        cookies = {k: '[PRESENT]' for k in request.cookies.keys()}
        
        # Check for JWT cookies 
        jwt_access = 'access_token_cookie' in request.cookies
        jwt_refresh = 'refresh_token_cookie' in request.cookies
        
        # Try to get identity if JWT is present
        jwt_identity = None
        jwt_error = None
        
        if jwt_access:
            try:
                verify_jwt_in_request(optional=True)
                jwt_identity = get_jwt_identity()
            except Exception as e:
                jwt_error = str(e)
        
        # Get headers (excluding actual cookie values)
        headers = {}
        for name, value in request.headers.items():
            if name.lower() != 'cookie':
                headers[name] = value
            else:
                headers[name] = '[COOKIE VALUES HIDDEN]'
        
        return jsonify({
            'cookies': cookies,
            'jwt_access_present': jwt_access,
            'jwt_refresh_present': jwt_refresh,
            'jwt_identity': jwt_identity,
            'jwt_error': jwt_error,
            'headers': headers,
            'cors_enabled': True,
            'same_site_setting': app.config.get('JWT_COOKIE_SAMESITE')
        })
    
    @app.route('/api/test-cookies', methods=['GET'])
    def test_cookies():
        """Test endpoint to set simple cookies for verification"""
        response = make_response(jsonify({
            'message': 'Testing cookies',
            'timestamp': datetime.now().isoformat()
        }))
        
        response.set_cookie(
            'test_cookie', 
            'test_value', 
            httponly=True, 
            secure=False,
            samesite='None',
            path='/'
        )
        
        response.set_cookie(
            'test_visible_cookie', 
            'frontend_visible',
            httponly=False,
            secure=False,
            samesite='None',
            path='/'
        )
        
        return response
```

## Implementation plan:

1. Create the new module files as outlined above
2. Move routes from the main routes.py file to these modules
3. Import and register these route modules in the main app.py
4. Remove the fix-cookies.js file
5. Update the frontend to remove debug components in production builds
