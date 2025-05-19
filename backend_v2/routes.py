"""
API routes definition for Quiz App
"""
import os
import sys
import traceback
from datetime import datetime
from flask import jsonify, request, redirect, make_response
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    get_jwt_identity, 
    jwt_required, 
    get_jwt,
    verify_jwt_in_request
)

from controllers.quiz_controller import QuizController
from controllers.user_controller import UserController
from controllers.oauth_controller import OAuthController
from models.user import User
from utils.helpers import admin_required, sanitize_input

def register_routes(app):
    """Register API routes in Flask application"""
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({'status': 'ok', 'message': 'Server is running'})
    
    # User endpoints
    @app.route('/api/users')
    def get_users():
        """Get all users"""
        users, error = UserController.get_all_users()
        if error:
            return jsonify({'error': error}), 500
        return jsonify({"users": users})
    
    @app.route('/api/users/<int:user_id>', methods=['GET'])
    def get_user_by_id(user_id):
        """Get user by ID"""
        app.logger.info(f"Getting user with ID: {user_id}")
        user = User.query.get(user_id)
        if not user:
            app.logger.warning(f"User with ID {user_id} not found")
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict()), 200
    
    @app.route('/api/users/<int:user_id>', methods=['PUT'])
    @jwt_required()
    def update_user_data_route(user_id):
        """Update user data (username, email)"""
        # Check if logged in user has permission to modify this data
        current_user_id = get_jwt_identity()
        if int(current_user_id) != int(user_id):
            app.logger.warning(f"Unauthorized attempt to update user data: user {current_user_id} tried to modify user {user_id}")
            return jsonify({'error': 'You do not have permission to update this user'}), 403
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_data, error = UserController.update_user_data(user_id, data)
        if error:
            status_code = 404 if error == "User not found" else 400
            if "Email already in use" in error:
                status_code = 409  # Conflict
            return jsonify({'error': error}), status_code
        return jsonify(user_data)
    
    @app.route('/api/users/<int:user_id>/change-password', methods=['PUT'])
    @jwt_required()
    def change_password_route(user_id):
        """Change user password"""
        # Check if logged in user has permission to change this password
        current_user_id = get_jwt_identity()
        if int(current_user_id) != int(user_id):
            app.logger.warning(f"Unauthorized attempt to change password: user {current_user_id} tried to modify user {user_id}")
            return jsonify({'error': 'You do not have permission to change this user\'s password'}), 403
            
        data = request.get_json()
        if not data or 'currentPassword' not in data or 'newPassword' not in data:
            return jsonify({'error': 'Missing currentPassword or newPassword'}), 400
        
        result, error = UserController.change_password(
            user_id,
            data['currentPassword'],
            data['newPassword']
        )
        if error:
            status_code = 404 if error == "User not found" else 400
            return jsonify({'error': error}), status_code
        return jsonify(result)
    
    @app.route('/api/users/<int:user_id>/avatar', methods=['PUT'])
    @jwt_required()
    def update_user_avatar(user_id):
        """Update user avatar"""
        # Check if logged in user has permission to modify this data
        current_user_id = get_jwt_identity()
        if int(current_user_id) != int(user_id):
            app.logger.warning(f"Unauthorized attempt to update avatar: user {current_user_id} tried to modify user {user_id}")
            return jsonify({'error': 'You do not have permission to update this user'}), 403
            
        data = request.get_json()
        if not data or 'avatar_url' not in data:
            return jsonify({'error': 'No avatar URL provided'}), 400
        
        # Sanitize input data
        avatar_url = sanitize_input(data['avatar_url'])
        if not avatar_url:
            return jsonify({'error': 'Invalid avatar URL'}), 400
        
        result, error = UserController.update_user_avatar(user_id, avatar_url)
        if error:
            return jsonify({'error': error}), 500
        return jsonify(result)
    
    @app.route('/api/users/me/profile', methods=['GET'])
    @jwt_required()
    def get_current_user_profile():
        """Get profile details for the current user"""
        # Get user ID from JWT
        user_id = get_jwt_identity()
        
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Find user in database
        user = User.query.get(user_id)
        if not user:
            app.logger.warning(f"User with ID {user_id} from token not found in database")
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
    
    @app.route('/api/register', methods=['POST'])
    def register():
        """Register new user"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user, error = UserController.register_user(data)
        if error:
            return jsonify({'error': error}), 409 if "already exists" in error else 400
            
        try:            # Create JWT tokens
            app.logger.info(f"Creating JWT tokens for new user {user.id}")
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))

            # Create response with properly structured user data
            user_data = user.to_dict()
            app.logger.info(f"User data structure after registration: {user_data}")
            resp = make_response(jsonify(user_data))

            # Set access token as HTTP-only cookie
            resp.set_cookie(
                'access_token_cookie', 
                access_token, 
                httponly=True, 
                secure=False,  # Set to True in production with HTTPS
                samesite='None'  # Required for cross-site requests
            )
            
            # Set refresh token as HTTP-only cookie
            resp.set_cookie(
                'refresh_token_cookie', 
                refresh_token, 
                httponly=True, 
                secure=False,  # Set to True in production with HTTPS
                samesite='None'  # Required for cross-site requests
            )
            
            return resp, 201
        except Exception as e:
            app.logger.error(f"Error creating JWT tokens: {str(e)}")
            # Return user data without tokens if there's an error
            return jsonify(user_data), 201
    
    @app.route('/api/login', methods=['POST'])
    def login():
        """Login user"""
        app.logger.info("Login request received")
        data = request.get_json()
        if not data:
            app.logger.warning("No data provided in login request")
            return jsonify({'error': 'No data provided'}), 400
        
        user, error = UserController.login_user(data.get('email'), data.get('password'))
        if error:
            status_code = 401 if "Invalid email or password" in error else 400
            app.logger.warning(f"Login failed: {error}, status code: {status_code}")
            return jsonify({'error': error}), status_code
            
        try:            # Create JWT tokens
            app.logger.info(f"Creating JWT tokens for user {user.id}")
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            # Create response with properly structured user data
            user_data = user.to_dict()
            app.logger.info(f"User data being returned: {user_data}")
            resp = jsonify(user_data=user_data)

            # Set access token as HTTP-only cookie
            resp.set_cookie(
                'access_token_cookie', 
                access_token, 
                httponly=True, 
                secure=False,  # Set to True in production with HTTPS
                samesite='None'  # Required for cross-site requests
            )
            
            # Set refresh token as HTTP-only cookie
            resp.set_cookie(
                'refresh_token_cookie', 
                refresh_token, 
                httponly=True, 
                secure=False,  # Set to True in production with HTTPS
                samesite='None'  # Required for cross-site requests
            )
            
            # Add a visible cookie for frontend detection
            resp.set_cookie(
                'auth_success', 
                'true', 
                httponly=False,
                secure=False,
                samesite='None',
                max_age=3600
            )
            
            app.logger.info(f"Login successful for user: {user.email}")
            return resp, 200
        except Exception as e:
            app.logger.error(f"Error creating JWT tokens: {str(e)}")
            return jsonify({'error': 'Internal server error during authentication'}), 500
    
    @app.route('/api/token/refresh', methods=['POST'])
    @jwt_required(refresh=True)    
    def refresh_token():
        """Refresh access token using refresh token"""
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=str(current_user_id))
        
        # Create response
        resp = make_response(jsonify({'message': 'Token refreshed successfully'}))

        # Set new access token as HTTP-only cookie
        resp.set_cookie(
            'access_token_cookie', 
            access_token, 
            httponly=True, 
            secure=False,  # Set to True in production with HTTPS
            samesite='None'  # Required for cross-site requests
        )
        
        return resp, 200    @app.route('/api/logout', methods=['POST'])
    def logout():
        """Logout user by clearing cookies"""
        resp = make_response(jsonify({'message': 'Logged out successfully'}))
        
        # Clear JWT cookies (HttpOnly)
        resp.delete_cookie('access_token_cookie', path='/', domain=None)
        resp.delete_cookie('refresh_token_cookie', path='/', domain=None)
        
        # Clear client-visible cookies
        resp.delete_cookie('auth_success', path='/', domain=None)
        resp.delete_cookie('visible_auth', path='/', domain=None)
        resp.delete_cookie('test_visible_cookie', path='/', domain=None)
        resp.delete_cookie('js_test_cookie', path='/', domain=None)
        
        # Set explicit header to clear cookies
        resp.headers.add('Set-Cookie', 'auth_success=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT;')
        resp.headers.add('Set-Cookie', 'visible_auth=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT;')
        
        app.logger.info("All cookies cleared during logout")
        return resp, 200
    
    # Debug endpoints (only for development)
    @app.route('/api/test-cookies', methods=['GET', 'OPTIONS'])
    def test_cookies():
        """Test endpoint to diagnose cookie issues"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            # Let the global after_request handler set the credentials header
            # to avoid duplicate headers
            return response
            response = make_response(jsonify({
            'message': 'Testing cookie setting',
            'timestamp': datetime.now().isoformat()
        }))
        
        # Set a test cookie
        response.set_cookie(
            'test_cookie', 
            'test_value', 
            httponly=True, 
            secure=False,  # Set to True in production with HTTPS
            samesite='None',  # Required for cross-site requests
            path='/'
        )
        
        # Add a non-httpOnly cookie to help the frontend detect cookie functionality
        response.set_cookie(
            'test_visible_cookie', 
            'frontend_visible',
            httponly=False,
            secure=False,
            samesite='None',
            path='/'
        )
        
        return response
    
    @app.route('/api/debug/auth', methods=['GET'])
    def debug_auth():
        """Debug endpoint to check authentication status and cookies"""
        if os.environ.get('FLASK_ENV') == 'production':
            return jsonify({'error': 'Debug endpoints not available in production'}), 403
            
        try:
            # Get cookie info
            cookies = {k: '[PRESENT]' for k in request.cookies.keys()}
            
            # Check for JWT cookies specifically
            jwt_access = 'access_token_cookie' in request.cookies
            jwt_refresh = 'refresh_token_cookie' in request.cookies
            
            # Try to get identity if JWT is present
            jwt_identity = None
            jwt_error = None
            
            if jwt_access:
                try:
                    from flask_jwt_extended import verify_jwt_in_request
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
                'cors_enabled': True,  # CORS is enabled in this application
                'same_site_setting': app.config.get('JWT_COOKIE_SAMESITE')
            })
        except Exception as e:
            app.logger.error(f"Error in debug endpoint: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    # Additional debug endpoint for cookie testing
    @app.route('/api/debug/set-visible-cookie', methods=['GET', 'OPTIONS'])
    def set_visible_cookie():
        """Endpoint to set a visible client-side cookie for testing purposes"""
        if os.environ.get('FLASK_ENV') == 'production':
            return jsonify({'error': 'Debug endpoints not available in production'}), 403
            
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            return response
            
        # Create a response with a visible cookie
        response = make_response(jsonify({
            'message': 'Client-visible cookie set',
            'timestamp': datetime.now().isoformat()
        }))
        
        # Set a visible cookie with appropriate attributes
        response.set_cookie(
            'client_visible_cookie', 
            f'set_by_server_{datetime.now().second}',
            httponly=False,  # Crucial - this makes it visible to JavaScript
            secure=False,    # Set to True if using HTTPS
            samesite='None', # Required for cross-site requests
            path='/',
            max_age=3600     # 1 hour expiry
        )
        
        # Set auth_success cookie too
        response.set_cookie(
            'auth_success', 
            'true', 
            httponly=False,  # Must be visible to client-side JavaScript
            secure=False,    # Set to True if using HTTPS
            samesite='None', # Required for cross-site requests
            path='/',
            max_age=3600     # 1 hour expiry
        )
        
        return response
    
    # Additional debug endpoint for cookie testing    @app.route('/api/test-auth-cookies', methods=['GET', 'OPTIONS'])
    def test_auth_cookies():
        """Test endpoint specifically for diagnosing authentication cookie issues"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            # Don't add any CORS headers here - let the global after_request handle it
            return response
            
        # Check if there are valid JWT cookies
        jwt_valid = False
        user_id = None
        error_msg = None
        
        try:
            # Try to verify JWT
            verify_jwt_in_request(optional=True)
            current_user = get_jwt_identity()
            if current_user:
                jwt_valid = True
                user_id = current_user
            else:
                error_msg = "No JWT identity found"
        except Exception as e:
            error_msg = str(e)
            
        # Get all cookies for debugging
        cookie_info = {}
        for name, value in request.cookies.items():
            if name in ['access_token_cookie', 'refresh_token_cookie']:
                # Don't show actual token values for security
                cookie_info[name] = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "[PRESENT]"
            else:
                cookie_info[name] = value
                
        # Create a test auth cookie
        response = make_response(jsonify({
            'message': 'Testing auth cookies',
            'timestamp': datetime.now().isoformat(),
            'jwt_valid': jwt_valid,
            'user_id': user_id,
            'error': error_msg,
            'cookies': cookie_info,
            'headers': {k: v for k, v in request.headers.items() if k.lower() != 'cookie'}
        }))
          # Set a visible cookie for the frontend to detect
        response.set_cookie(
            'auth_success', 
            'true', 
            httponly=False, 
            path='/',
            secure=False,
            samesite='None',
            max_age=3600  # Set cookie to expire in 1 hour
        )
        
        # Set a separate test cookie
        response.set_cookie(
            'test_visible_cookie', 
            f'frontendvisible_{datetime.now().second}',
            httponly=False,
            secure=False,
            samesite='None',
            path='/'
        )
        
        return response
    
    # OAuth endpoints
    @app.route('/api/login/google')
    def login_with_google():
        """Initiate Google OAuth login process"""
        return OAuthController.login_with_google()
    @app.route('/api/authorize/google')
    def authorize_google():
        """Handle callback after Google authorization"""
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        try:
            result = OAuthController.handle_google_callback()
            if result is None:
                app.logger.error("OAuth callback returned None instead of (user, error)")
                return redirect(f"{frontend_url}/login?error=Internal+server+error")
                
            user, error_message = result
            app.logger.info(f"Google callback result: User: {user is not None}, Error: {error_message}")
            
            if error_message:
                # Redirect to frontend with error
                error_query = f"?error={error_message}"
                app.logger.error(f"Redirecting to frontend with error: {error_message}")
                return redirect(f"{frontend_url}/login{error_query}")
              # Create JWT tokens like normal login
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            app.logger.info(f"Created tokens for OAuth user {user.email}")
            
            # Create response with redirect 
            redirect_url = f"{frontend_url}/oauth-callback"
            resp = make_response(redirect(redirect_url))
            
            # Set access token cookie with all necessary attributes directly
            resp.set_cookie(
                'access_token_cookie', 
                access_token, 
                httponly=True, 
                path='/',
                secure=False,  # Set to True in production with HTTPS
                samesite='None'  # Required for cross-site requests
            )
            
            # Set refresh token cookie with all necessary attributes directly
            resp.set_cookie(
                'refresh_token_cookie', 
                refresh_token, 
                httponly=True, 
                path='/',
                secure=False,  # Set to True in production with HTTPS
                samesite='None'  # Required for cross-site requests
            )              # Add a non-httpOnly cookie to help the frontend detect successful auth
            resp.set_cookie(
                'auth_success', 
                'true', 
                httponly=False, 
                path='/',
                secure=False,
                samesite='None',
                max_age=3600  # Set to expire in 1 hour
            )
            
            # Set another visible cookie with a different method that might be more compatible
            # with certain browsers that block third-party cookies
            resp.headers.add('Set-Cookie', 
                'visible_auth=true; Path=/; Max-Age=3600; SameSite=None')
            
            # Log cookies being set
            app.logger.info(f"Setting cookies for user {user.id}. Redirecting to: {redirect_url}")
            
            # Ensure CORS headers are set
            resp.headers.add('Access-Control-Allow-Credentials', 'true')
            
            return resp
        except Exception as e:
            app.logger.exception(f"Error in Google OAuth callback handling: {str(e)}")
            return redirect(f"{frontend_url}/login?error=Internal+OAuth+Error")
    
    # Quiz endpoints
    @app.route('/api/quiz', methods=['GET'])
    def get_quizzes():
        """Get all quizzes with optional filtering"""
        category = sanitize_input(request.args.get('category'))
        difficulty = sanitize_input(request.args.get('difficulty'))
        search = sanitize_input(request.args.get('search'))
        
        quizzes, error = QuizController.get_all_quizzes(
            category=category,
            difficulty=difficulty,
            search=search
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'quizzes': quizzes})
    
    @app.route('/api/quiz/<int:quiz_id>', methods=['GET'])
    def get_quiz(quiz_id):
        """Get quiz by ID"""
        app.logger.info(f"Getting quiz with ID: {quiz_id}")
        
        quiz, error = QuizController.get_quiz_by_id(quiz_id)
        
        if error:
            app.logger.error(f"Error getting quiz {quiz_id}: {error}")
            return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
        
        return jsonify(quiz)
    
    @app.route('/api/quiz', methods=['POST'])
    @jwt_required()
    def create_quiz():
        """Create new quiz"""
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add current user ID as author
        current_user_id = get_jwt_identity()
        data['author_id'] = current_user_id
        
        quiz, error = QuizController.create_quiz(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify(quiz), 201
    
    @app.route('/api/quiz/<int:quiz_id>', methods=['PUT'])
    @jwt_required()
    def update_quiz(quiz_id):
        """Update existing quiz"""
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Check if user is quiz author or admin
        current_user_id = get_jwt_identity()
        quiz, _ = QuizController.get_quiz_by_id(quiz_id)
        if quiz:
            user = User.query.get(current_user_id)
            if not user.is_admin and ('author_id' not in quiz or quiz['author_id'] != current_user_id):
                app.logger.warning(f"User {current_user_id} attempted to update quiz {quiz_id} without permission")
                return jsonify({'error': 'You do not have permission to update this quiz'}), 403
        
        quiz, error = QuizController.update_quiz(quiz_id, data)
        if error:
            return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
        
        return jsonify(quiz)
    
    @app.route('/api/quiz/<int:quiz_id>', methods=['DELETE'])
    @jwt_required()
    def delete_quiz(quiz_id):
        """Delete quiz"""
        # Check if user is quiz author or admin
        current_user_id = get_jwt_identity()
        quiz, _ = QuizController.get_quiz_by_id(quiz_id)
        if quiz:
            user = User.query.get(current_user_id)
            if not user.is_admin and ('author_id' not in quiz or quiz['author_id'] != current_user_id):
                app.logger.warning(f"User {current_user_id} attempted to delete quiz {quiz_id} without permission")
                return jsonify({'error': 'You do not have permission to delete this quiz'}), 403
        
        success, error = QuizController.delete_quiz(quiz_id)
        
        if error:
            return jsonify({'error': error}), 404 if error == "Quiz not found" else 400
        return jsonify({'message': 'Quiz deleted successfully'})

    # Test endpoint to debug user data structure
    @app.route('/api/user-debug', methods=['GET'])
    @jwt_required()
    def user_debug():
        """Debug endpoint for user data structure"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            # Return detailed user data for debugging
            user_dict = user.to_dict()
            return jsonify({
                'user_from_db': user_dict,
                'user_raw': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'avatar_url': user.avatar_url,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }            }), 200
        except Exception as e:            
            app.logger.error(f"Error in user debug endpoint: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    # Debug endpoints
    @app.route('/api/debug/auth-state')
    def debug_auth_state():
        """Get debug information about authentication cookies and tokens"""
        auth_info = {
            'cookies': {}
        }
        
        # Try to get JWT identity to check token validity
        try:
            verify_jwt_in_request(optional=True)
            jwt_identity = get_jwt_identity()
            auth_info['jwt_identity'] = jwt_identity        
        except Exception as e:
            app.logger.warning(f"JWT verification failed: {str(e)}")
            auth_info['jwt_error'] = str(e)
            
        # Get all cookies from request
        cookies = request.cookies
        for key, value in cookies.items():
            # Don't show the actual token values for security
            if key in ['access_token_cookie', 'refresh_token_cookie']:
                auth_info['cookies'][key] = '[REDACTED]'
                auth_info[f'jwt_{key.split("_")[0]}_present'] = True
            else:
                auth_info['cookies'][key] = value
        
        return jsonify(auth_info)
    
    @app.route('/api/debug/current-user')
    @jwt_required(optional=True)
    def debug_current_user():
        """Get debug information about the current user"""
        # Get user ID from JWT
        user_id = get_jwt_identity()
        
        debug_info = {
            'request': {
                'cookies': {k: '[REDACTED]' if 'token' in k.lower() else v 
                           for k, v in request.cookies.items()},
                'headers': {k: v for k, v in request.headers.items() 
                           if k.lower() not in ['authorization', 'cookie']}
            },
            'auth': {
                'user_id': user_id,
                'authenticated': user_id is not None
            }
        }
        
        # If user is authenticated, add user data
        if user_id:
            user = User.query.get(user_id)
            if user:
                debug_info['user'] = user.to_dict()
                # Add additional debug fields that might be useful
                debug_info['user']['_extra'] = {
                    'created_at_raw': user.created_at.isoformat() if user.created_at else None,
                    'password_hash_exists': user.password_hash is not None,
                    'social_provider': user.social_provider
                }
            else:
                debug_info['auth']['error'] = 'User ID from token not found in database'
        
        return jsonify(debug_info)
