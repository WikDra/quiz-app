"""
API routes definition for Quiz App
"""
import os
import sys
from flask import jsonify, request, redirect, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required

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
    def get_my_profile():
        """Get profile of logged in user"""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            app.logger.warning(f"User with ID {current_user_id} not found")
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
            
        try:
            # Create JWT tokens
            app.logger.info(f"Creating JWT tokens for new user {user.id}")
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)

            # Create response
            user_data = user.to_dict()
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
            
        try:
            # Create JWT tokens
            app.logger.info(f"Creating JWT tokens for user {user.id}")
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
            # Create response
            resp = jsonify(user_data=user.to_dict())

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
        access_token = create_access_token(identity=current_user_id)
        
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
        
        return resp, 200
    
    @app.route('/api/logout', methods=['POST'])
    def logout():
        """Logout user by clearing cookies"""
        resp = make_response(jsonify({'message': 'Logged out successfully'}))
        resp.delete_cookie('access_token_cookie')
        resp.delete_cookie('refresh_token_cookie')
        return resp, 200
    
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
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            app.logger.info(f"Created tokens for OAuth user {user.email}")
            
            # Create response with redirect
            resp = make_response(redirect(f"{frontend_url}/oauth-callback"))
            
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

            # Redirect to frontend
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
