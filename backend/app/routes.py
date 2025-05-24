from flask import request, jsonify, make_response, url_for, redirect
from flask_restful import Resource
from .models import db, User
from .extensions import oauth2
from flask_jwt_extended import create_access_token, jwt_required, create_refresh_token, get_jwt_identity, get_jwt
import logging
import re
import os
from .quiz_controller import QuizController
logging.basicConfig(level=logging.DEBUG)





class RegisterResource(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)
        if not username or not valid or not password:
            return {'message': 'All fields are required'}, 400

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return {'message': 'Username or email already exists'}, 400

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return {'message': 'User registered successfully'}, 201
class LoginResource(Resource):
    def post(self):
        # Pobieranie danych z żądania
        data = request.get_json()
        
        if not data:
            return make_response(jsonify({'message': 'No JSON data provided'}), 400)

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return make_response(jsonify({'message': 'Username and password are required'}), 400)

        # Wyszukiwanie użytkownika w bazie danych
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Generowanie tokenu JWT
            access_token = create_access_token(identity=user.id,expires_delta=None)
            refresh_token = create_refresh_token(identity=user.id)
            response = make_response(jsonify({'access_token': access_token,
                                          'refresh_token': refresh_token}), 200)
            response.set_cookie("access_token_cookie", access_token)
            response.set_cookie("refresh_token_cookie", refresh_token)
            return response

        else:
            return make_response(jsonify({'message': 'Invalid credentials'}), 401)
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
            access_token = create_access_token(identity=user.google_id)
            refresh_token = create_refresh_token(identity=user.google_id)
            response = make_response(redirect('http://localhost:5173/oauth-callback'))
            response.set_cookie("access_token_cookie", access_token)
            response.set_cookie("refresh_token_cookie", refresh_token)
            return response
        else:
            access_token = create_access_token(identity=userinfo.get("sub"))
            refresh_token = create_refresh_token(identity=userinfo.get("sub"))
            user = User.query.filter_by(google_id=userinfo['sub']).first()
            response = make_response(redirect('http://localhost:5173/oauth-callback'))
            response.set_cookie("access_token_cookie", access_token)
            response.set_cookie("refresh_token_cookie", refresh_token)
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
                user_id = get_jwt_identity()
                if not user_id:
                    return jsonify({'error': 'Authentication required'}), 401
                user = User.query.get(user_id)
                if not user:
                    logging.warning(f"Current user with ID {user_id} not found in database")
                    return jsonify({'error': 'User not found'}), 404
            
            return jsonify(user.to_dict()), 200
        except Exception as e:
            logging.error(f"Error in get_user: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

class UserMeResource(Resource):
    @jwt_required(locations=["cookies"])
    def get(self):
        """Get profile of logged in user"""
        current_user_id = get_jwt_identity()
        user = User.query.filter_by(google_id=current_user_id).first()
        if not user:
            logging.warning(f"User with ID {current_user_id} not found")
            return jsonify({'error': 'User not found'}), 404
        return user.to_dict(), 200
    
class LogoutResource(Resource):
    @jwt_required(locations=["cookies"])
    def post(self):
        resp = make_response(jsonify({'message': 'Logged out successfully'}))
        # Clear JWT cookies (HttpOnly)
        resp.delete_cookie('access_token_cookie', path='/', domain=None, samesite='None')
        resp.delete_cookie('refresh_token_cookie', path='/', domain=None, samesite='None')
        
        # Clear client-visible cookies
        resp.delete_cookie('auth_success', path='/', domain=None, samesite='None')
        resp.delete_cookie('visible_auth', path='/', domain=None, samesite='None')
        resp.delete_cookie('test_visible_cookie', path='/', domain=None, samesite='None')
        resp.delete_cookie('js_test_cookie', path='/', domain=None, samesite='None')
        
        # Set explicit header to clear cookies
        resp.headers.add('Set-Cookie', 'auth_success=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT;')
        resp.headers.add('Set-Cookie', 'visible_auth=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT;')
        
        logging.info("All cookies cleared during logout")
        return resp, 200
        
    
class CookieTest(Resource):
    def get(self):
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
            'test_cookie',            'test_value', 
            httponly=True, 
            secure=True,  # Must be True for SameSite=None to work
            samesite='None',  # Required for cross-site requests
            path='/'
        )
        
        # Add a non-httpOnly cookie to help the frontend detect cookie functionality
        response.set_cookie(
            'test_visible_cookie', 
            'frontend_visible',
            httponly=False,
            secure=True,  # Must be True for SameSite=None to work
            samesite='None',
            path='/'
        )
        
        return response
