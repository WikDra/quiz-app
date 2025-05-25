from flask import request, jsonify, make_response, url_for, redirect
from flask_restful import Resource
from .extensions import oauth2
from flask_jwt_extended import create_access_token, jwt_required, create_refresh_token, get_jwt_identity, get_jwt
import logging
import os
from datetime import datetime
from .user_controller import UserController, TokenBlacklistManager
from .models import User, OfflinePayment
from .extensions import db
from utils.helpers import sanitize_input, validate_email
from .quiz_controller import QuizController
from .admin_controller import AdminController
from .admin_middleware import admin_required
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

            # Create response with make_response and include tokens in JSON
            user_data = user.to_dict()
            resp = make_response({
                'message': 'Registration successful',
                'user': user_data,
                'access_token': access_token,
                'refresh_token': refresh_token
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

            # Create response with tokens included in JSON
            resp = make_response({
                'message': 'Login successful',
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
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
        if not user:
            return {'error': 'User not found'}, 404
        return {"Nazwa użytkownika": user.username, "E-mail": user.email}, 200
    
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
    
    @jwt_required(locations=["cookies"])
    def put(self, user_id):
        """Update user's own data"""
        try:
            # Get current user from JWT
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return {'error': 'Authentication required'}, 401
            
            # Convert current_user_id to int for comparison
            try:
                current_user_numeric = int(current_user_id)
            except (ValueError, TypeError):
                return {'error': 'Invalid user authentication'}, 401
            
            # Check if user is trying to update their own data
            if current_user_numeric != user_id:
                return {'error': 'You can only update your own data'}, 403
            
            # Get request data
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Use UserController to update user data
            from .user_controller import UserController
            result, error = UserController.update_user_data(user_id, data)
            
            if error:
                return {'error': error}, 400
            
            return {'message': 'User updated successfully', 'user': result}, 200
            
        except Exception as e:
            logging.error(f"Error updating user {user_id}: {str(e)}")
            return {'error': 'Failed to update user'}, 500

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

# ============= USER ENDPOINTS =============

class UserOfflinePaymentRequestResource(Resource):
    @jwt_required(locations=["cookies"])
    def post(self):
        """Allow users to request offline payment for premium access"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Check if user already has premium
            if user.has_premium_access:
                return {'error': 'User already has premium access'}, 400
            
            # Check if user already has a pending offline payment request
            existing_request = OfflinePayment.query.filter_by(
                user_id=user.id,
                status='pending'
            ).first()
            
            if existing_request:
                return {'error': 'You already have a pending offline payment request'}, 400
            
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Validate required fields
            required_fields = ['amount', 'paymentMethod', 'description']
            for field in required_fields:
                if field not in data or not data[field]:
                    return {'error': f'Missing required field: {field}'}, 400
            
            # Create offline payment request
            offline_payment = OfflinePayment(
                user_id=user.id,
                amount=float(data['amount']),
                payment_method=data['paymentMethod'],
                description=data['description'],
                reference_number=data.get('referenceNumber', ''),
                status='pending',
                admin_id=1  # Will be updated when admin processes it
            )
            
            db.session.add(offline_payment)
            db.session.commit()
            
            return {
                'message': 'Offline payment request submitted successfully',
                'request_id': offline_payment.id
            }, 201
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating offline payment request: {str(e)}")
            return {'error': 'Failed to submit offline payment request'}, 500

# ============= ADMIN ENDPOINTS =============

class AdminDashboardResource(Resource):
    @jwt_required(locations=["cookies"])
    @admin_required
    def get(self):
        """Get admin dashboard statistics"""
        try:
            stats = AdminController.get_dashboard_stats()
            return stats, 200
        except Exception as e:
            logging.error(f"Error getting dashboard stats: {str(e)}")
            return {'error': 'Failed to load dashboard stats'}, 500

class AdminUsersResource(Resource):
    @jwt_required(locations=["cookies"])
    @admin_required
    def get(self):
        """Get all users with pagination"""
        try:
            users_data = AdminController.get_users()
            # Return just the list of users for tests compatibility
            if 'users' in users_data:
                return users_data['users'], 200
            else:
                return users_data, 200
        except Exception as e:
            logging.error(f"Error getting users: {str(e)}")
            return {'error': 'Failed to load users'}, 500

class AdminUserPromoteResource(Resource):
    @jwt_required(locations=["cookies"])
    @admin_required
    def post(self, user_id):
        """Promote user to admin"""
        try:
            result = AdminController.promote_user_to_admin(user_id)
            return result, 200
        except Exception as e:
            logging.error(f"Error promoting user {user_id}: {str(e)}")
            return {'error': 'Failed to promote user'}, 500

class AdminUserDemoteResource(Resource):
    @jwt_required(locations=["cookies"])
    @admin_required
    def post(self, user_id):
        """Demote admin to user"""
        try:
            result = AdminController.demote_admin_to_user(user_id)
            return result, 200
        except Exception as e:
            logging.error(f"Error demoting user {user_id}: {str(e)}")
            return {'error': 'Failed to demote user'}, 500

class AdminOfflinePaymentsResource(Resource):
    @jwt_required(locations=["cookies"])
    @admin_required
    def get(self):
        """Get offline payments"""
        try:
            payments_data = AdminController.get_offline_payments()
            # Return just the list of payments for tests compatibility
            if 'payments' in payments_data:
                return payments_data['payments'], 200
            else:
                return payments_data, 200
        except Exception as e:
            logging.error(f"Error getting offline payments: {str(e)}")
            return {'error': 'Failed to load payments'}, 500
    
    @jwt_required(locations=["cookies"])
    @admin_required
    def post(self):
        """Create new offline payment"""
        try:
            result = AdminController.create_offline_payment()
            return result, 201
        except Exception as e:
            logging.error(f"Error creating offline payment: {str(e)}")
            return {'error': 'Failed to create payment'}, 500

class AdminOfflinePaymentApproveResource(Resource):
    @jwt_required(locations=["cookies"])
    @admin_required
    def post(self, payment_id):
        """Approve offline payment"""
        try:
            result = AdminController.approve_offline_payment(payment_id)
            return result, 200
        except Exception as e:
            logging.error(f"Error approving payment {payment_id}: {str(e)}")
            return {'error': 'Failed to approve payment'}, 500

class AdminOfflinePaymentRejectResource(Resource):
    @jwt_required(locations=["cookies"])
    @admin_required
    def post(self, payment_id):
        """Reject offline payment"""
        try:
            result = AdminController.reject_offline_payment(payment_id)
            return result, 200
        except Exception as e:
            logging.error(f"Error rejecting payment {payment_id}: {str(e)}")
            return {'error': 'Failed to reject payment'}, 500

class AdminFailedPaymentsResource(Resource):
    @jwt_required(locations=["cookies"])
    @admin_required
    def get(self):
        """Get failed payments for admin dashboard"""
        try:
            payments_data = AdminController.get_failed_payments()
            # Combine failed_payments and failed_subscriptions into one list for tests compatibility
            if isinstance(payments_data, dict) and 'failed_payments' in payments_data:
                combined_list = payments_data.get('failed_payments', []) + payments_data.get('failed_subscriptions', [])
                return combined_list, 200
            else:
                return payments_data, 200
        except Exception as e:
            logging.error(f"Error getting failed payments: {str(e)}")
            return {'error': 'Failed to load failed payments'}, 500

class AdminUserEditResource(Resource):
    @jwt_required(locations=["cookies"])
    @admin_required
    def put(self, user_id):
        """Update user information"""
        try:
            result = AdminController.update_user(user_id)
            return result, 200
        except Exception as e:
            logging.error(f"Error updating user {user_id}: {str(e)}")
            return {'error': 'Failed to update user'}, 500

