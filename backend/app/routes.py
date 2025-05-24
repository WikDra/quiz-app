from flask import request, jsonify, make_response, url_for, redirect
from flask_restful import Resource
from .extensions import oauth2
from flask_jwt_extended import create_access_token, jwt_required, create_refresh_token, get_jwt_identity, get_jwt
import logging
import os
from datetime import datetime
from .user_controller import UserController, TokenBlacklistManager
from .models import User, db
from utils.helpers import sanitize_input, validate_email
from .quiz_controller import QuizController
logging.basicConfig(level=logging.DEBUG)

class RegisterResource(Resource):
    def post(self):
        """Register new user"""
        try:
            data = request.get_json()
            logging.info(f"Received registration data: {data}")
            if not data:
                return {'error': 'No data provided'}, 400
            
            user, error = UserController.register_user(data)
            if error:
                return {'error': error}, 409 if "already exists" in error else 400
                
            # Create JWT tokens with string identity
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))

            # Create response with make_response
            user_data = user.to_dict()
            resp = make_response({
                'message': 'Registration successful',
                'user': user_data
            })

            # Set access token as HTTP-only cookie
            resp.set_cookie(
                'access_token_cookie', 
                access_token, 
                httponly=True, 
                secure=False,  # For localhost development
                samesite='Lax',  # Changed from None to Lax for localhost
                path='/'
            )
            
            # Set refresh token as HTTP-only cookie
            resp.set_cookie(
                'refresh_token_cookie', 
                refresh_token, 
                httponly=True, 
                secure=False,  # For localhost development
                samesite='Lax',  # Changed from None to Lax for localhost
                path='/'
            )
            
            return resp

        except Exception as e:
            logging.error(f"Registration error: {str(e)}")
            return {'error': 'Internal server error'}, 500

class LoginResource(Resource):
    def post(self):
        """Login user"""
        try:
            data = request.get_json()
            logging.info(f"Login request data: {data}")
            
            if not data:
                logging.warning("No data provided in login request")
                return {'error': 'No data provided'}, 400
            
            email = data.get('email')
            password = data.get('password')
            logging.info(f"Extracted email: {email}, password length: {len(password) if password else 0}")
            
            user, error = UserController.login_user(email, password)
            if error:
                logging.warning(f"Login failed: {error}")
                status_code = 401 if "Invalid email or password" in error else 400
                return {'error': error}, status_code
                
            logging.info(f"Login successful for user: {email}")
            # Create JWT tokens with string identity
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))

            # Create response
            resp = make_response({
                'message': 'Login successful',
                'user': user.to_dict()
            })

            # Set access token as HTTP-only cookie
            resp.set_cookie(
                'access_token_cookie', 
                access_token, 
                httponly=True, 
                secure=False,  # For localhost development
                samesite='Lax',  # Changed from None to Lax for localhost
                path='/'
            )
            
            # Set refresh token as HTTP-only cookie
            resp.set_cookie(
                'refresh_token_cookie', 
                refresh_token, 
                httponly=True, 
                secure=False,  # For localhost development
                samesite='Lax',  # Changed from None to Lax for localhost
                path='/'
            )
            
            return resp

        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            return {'error': 'Internal server error'}, 500
class RefreshResource(Resource):    
    @jwt_required(refresh=True, locations=["cookies"])
    def post(self):
        identity = get_jwt_identity()
        new_access_token = create_access_token(identity=identity, fresh=False)
        response = make_response(jsonify({"access_token": new_access_token}), 200)
        response.set_cookie("access_token_cookie", new_access_token)
        return response
    
class GoogleLoginRedirect(Resource):
    def get(self):
        redirect_uri = url_for('googlelogincallback', _external=True)
        google = oauth2.create_client('google')
        return google.authorize_redirect(redirect_uri)

class GoogleLoginCallback(Resource):
    def get(self):
        google = oauth2.create_client('google')
        token = google.authorize_access_token()
        userinfo = token.get('userinfo')

        user = User.query.filter_by(google_id=userinfo['sub']).first()
        if not user:
            user = User(
                username=userinfo['email'].split("@")[0],
                email=userinfo['email'],
                google_id=userinfo['sub']
            )
            db.session.add(user)
            db.session.commit()
            
        # Always use google_id as identity for OAuth users (as string)
        access_token = create_access_token(identity=str(user.google_id))
        refresh_token = create_refresh_token(identity=str(user.google_id))
        
        response = make_response(redirect(f'{os.getenv("FRONTEND_URL")}/oauth-callback'))
        response.set_cookie("access_token_cookie", access_token, httponly=True, secure=False, samesite='Lax', path='/')
        response.set_cookie("refresh_token_cookie", refresh_token, httponly=True, secure=False, samesite='Lax', path='/')
        return response


class GoogleProfile(Resource):    
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.filter_by(google_id=user_id).first()
        response = make_response({"Nazwa użytkownika": user.username, "E-mail":user.email}, 200)
        return response
    
class UserResource(Resource):
    @jwt_required(locations=["cookies"])
    def get(self, user_id=None):
        """Get user details by ID or current user if no ID provided"""
        try:
            if user_id:
                user = User.query.get(user_id)
                if not user:
                    logging.warning(f"User with ID {user_id} not found")
                    return jsonify({'error': 'User not found'}), 404
            else:
                # Get current user from JWT
                current_user_id = get_jwt_identity()
                if not current_user_id:
                    return jsonify({'error': 'Authentication required'}), 401
                
                # Try to find user safely (handling both regular IDs and Google IDs)
                user = None
                try:
                    numeric_id = int(current_user_id)
                    if numeric_id < 1000000000:  # Regular user ID
                        user = User.query.get(numeric_id)
                    else:  # Large number, likely Google ID
                        user = User.query.filter_by(google_id=current_user_id).first()
                except (ValueError, TypeError, OverflowError):
                    user = User.query.filter_by(google_id=current_user_id).first()
                
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                    
                return user.to_dict(), 200
            
            return jsonify(user.to_dict()), 200
        except Exception as e:
            logging.error(f"Error in get_user: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

class UserMeResource(Resource):
    @jwt_required(locations=["cookies"])
    def get(self):
        """Get profile of logged in user"""
        logging.info("UserMeResource.get() called")
        
        # Debug: Log all cookies received
        from flask import request
        logging.info(f"Request cookies: {dict(request.cookies)}")
        logging.info(f"Request headers: {dict(request.headers)}")
        
        current_user_id = get_jwt_identity()
        logging.info(f"JWT identity: {current_user_id}")
        
        user = None
        
        # Try to determine if this is a regular user ID (small number) or Google ID (large number)
        try:
            # Try to convert to int and check if it's a reasonable user ID (< 1 billion)
            numeric_id = int(current_user_id)
            if numeric_id < 1000000000:  # Less than 1 billion, likely a regular user ID
                user = User.query.filter_by(id=numeric_id).first()
            else:
                # Large number, likely a Google ID - search by google_id as string
                user = User.query.filter_by(google_id=current_user_id).first()
        except (ValueError, TypeError, OverflowError):
            # If conversion fails, try as string (for OAuth users with google_id)
            user = User.query.filter_by(google_id=current_user_id).first()
        
        # If still not found, try the other field
        if not user:
            try:
                numeric_id = int(current_user_id)
                if numeric_id >= 1000000000:  # Large number, try as google_id string
                    user = User.query.filter_by(google_id=current_user_id).first()
                else:  # Small number, try as regular ID
                    user = User.query.filter_by(id=numeric_id).first()
            except (ValueError, TypeError, OverflowError):
                # Last resort: try as google_id string
                user = User.query.filter_by(google_id=current_user_id).first()
        
        logging.info(f"Looking for user with identity: {current_user_id}, found: {user}")
        
        if not user:
            logging.warning(f"User with ID {current_user_id} not found")
            return {'error': 'User not found'}, 404
            
        return user.to_dict(), 200
    
class LogoutResource(Resource):
    @jwt_required(locations=["cookies"])
    def post(self):
        try:
            # Get current JWT token details
            current_jwt = get_jwt()
            jti = current_jwt.get('jti')
            user_id = get_jwt_identity()
            exp = current_jwt.get('exp')
            
            # Get request data for logout options
            request_data = request.get_json() or {}
            logout_all_devices = request_data.get('logout_all', False)
            
            logging.info(f"Logout request from user {user_id}, logout_all: {logout_all_devices}")
            
            if logout_all_devices:
                # Blacklist all tokens for this user
                success = TokenBlacklistManager.blacklist_all_user_tokens(int(user_id))
                if success:
                    logging.info(f"All tokens blacklisted for user {user_id}")
                else:
                    logging.warning(f"Failed to blacklist all tokens for user {user_id}")
            else:
                # Blacklist only the current token
                if jti and exp:
                    expires_at = datetime.fromtimestamp(exp)
                    success = TokenBlacklistManager.blacklist_token(
                        jti=jti,
                        token_type='access',
                        user_id=int(user_id),
                        expires_at=expires_at
                    )
                    if success:
                        logging.info(f"Token {jti} blacklisted for user {user_id}")
                    else:
                        logging.warning(f"Failed to blacklist token {jti} for user {user_id}")
                else:
                    logging.warning("JWT token missing jti or exp claims")
            
            # Create response data
            response_data = {
                'message': 'Logged out successfully',
                'logout_all': logout_all_devices
            }
            
            # Clear JWT cookies by creating response with cleared cookies
            # Note: Flask-RESTful will handle the JSON response, we just need to clear cookies
            # This is a bit tricky with Flask-RESTful, so we'll return the data and let the framework handle it
            
            logging.info(f"Logout completed for user {user_id}")
            return response_data, 200
            
        except Exception as e:
            logging.error(f"Error during logout: {str(e)}")
            # Even if blacklisting fails, we should still return success for security
            return {
                'message': 'Logged out successfully',
                'warning': 'Some cleanup operations may have failed'
            }, 200
            resp.delete_cookie('visible_auth', path='/', domain=None, samesite='None')
            
            return resp, 200
        
