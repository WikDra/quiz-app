"""
Controller for user management
"""
import re
from flask import current_app
from flask_jwt_extended import get_jwt
from utils.helpers import sanitize_input, validate_email
from .models import User, db, BlacklistedToken
import logging
from datetime import datetime, timedelta

class TokenBlacklistManager:
    """
    Manager for JWT token blacklisting operations
    """
    
    @staticmethod
    def blacklist_token(jti, token_type, user_id, expires_at):
        """
        Add a token to the blacklist
        
        Args:
            jti (str): JWT ID
            token_type (str): Type of token ('access' or 'refresh')
            user_id (int or str): User ID who owns the token
            expires_at (datetime): When the token expires
        """
        try:
            # Convert user_id to string to handle large OAuth IDs
            user_id_str = str(user_id)
            
            blacklisted_token = BlacklistedToken(
                jti=jti,
                token_type=token_type,
                user_id=user_id_str,
                expires_at=expires_at
            )
            db.session.add(blacklisted_token)
            db.session.commit()
            
            current_app.logger.info(f"Token {jti} blacklisted for user {user_id_str}")
            return True
        except Exception as e:
            current_app.logger.error(f"Error blacklisting token {jti}: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def blacklist_all_user_tokens(user_id):
        """
        Blacklist all active tokens for a specific user
        This is useful for "logout from all devices" functionality
        
        Args:
            user_id (int or str): User ID whose tokens should be blacklisted
        """
        try:
            # Convert user_id to string to handle large OAuth IDs
            user_id_str = str(user_id)
            
            # Create a special blacklist entry that invalidates all tokens for this user
            # We use a special jti pattern to mark all tokens for this user as invalid
            # Set short expiry to avoid blocking future logins
            special_jti = f"user_logout_all_{user_id_str}_{datetime.utcnow().timestamp()}"
            
            blacklisted_token = BlacklistedToken(
                jti=special_jti,
                token_type='all_user_tokens',
                user_id=user_id_str,
                expires_at=datetime.utcnow() + timedelta(hours=1)  # Only 1 hour to avoid blocking future logins
            )
            db.session.add(blacklisted_token)
            db.session.commit()
            
            current_app.logger.info(f"All tokens blacklisted for user {user_id_str}")
            return True
        except Exception as e:
            current_app.logger.error(f"Error blacklisting all tokens for user {user_id}: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def is_token_blacklisted(jti, user_id=None):
        """
        Check if a token is blacklisted
        
        Args:
            jti (str): JWT ID to check
            user_id (int or str, optional): User ID for additional checks
            
        Returns:
            bool: True if token is blacklisted
        """
        try:
            # Check direct blacklist
            if BlacklistedToken.is_blacklisted(jti):
                return True
            
            # Check if all user tokens are blacklisted
            if user_id:
                # Convert user_id to string to handle large OAuth IDs
                user_id_str = str(user_id)
                
                user_blacklist = BlacklistedToken.query.filter(
                    BlacklistedToken.user_id == user_id_str,
                    BlacklistedToken.token_type == 'all_user_tokens',
                    BlacklistedToken.expires_at > datetime.utcnow()
                ).first()
                
                if user_blacklist:
                    current_app.logger.info(f"Token {jti} blacklisted via user-wide blacklist for user {user_id_str}")
                    return True
            
            return False
        except Exception as e:
            current_app.logger.error(f"Error checking blacklist status for token {jti}: {str(e)}")
            # On error, be safe and consider token valid to avoid blocking legitimate users
            return False
    
    @staticmethod
    def cleanup_expired_tokens():
        """
        Remove expired tokens from blacklist
        This should be called periodically to keep the database clean
        
        Returns:
            int: Number of tokens removed
        """
        try:
            expired_count = BlacklistedToken.cleanup_expired_tokens()
            current_app.logger.info(f"Cleaned up {expired_count} expired blacklisted tokens")
            return expired_count
        except Exception as e:
            current_app.logger.error(f"Error cleaning up expired tokens: {str(e)}")
            return 0

def setup_jwt_blacklist_callbacks(jwt_manager):
    """
    Setup JWT blacklist callbacks
    This function should be called when initializing the JWT manager
    
    Args:
        jwt_manager: Flask-JWT-Extended instance
    """
    
    @jwt_manager.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """
        Callback to check if a JWT exists in the blacklist
        This is called automatically by Flask-JWT-Extended for every protected route
        """
        jti = jwt_payload.get('jti')
        user_id = jwt_payload.get('sub')  # 'sub' is the standard JWT claim for user ID
        
        if not jti:
            current_app.logger.warning("JWT token without jti claim encountered")
            return True  # Block tokens without jti
        
        try:
            # Convert user_id to int if it's a string
            if user_id and isinstance(user_id, str):
                user_id = int(user_id)
        except (ValueError, TypeError):
            current_app.logger.warning(f"Invalid user_id in JWT payload: {user_id}")
            user_id = None
        
        is_blacklisted = TokenBlacklistManager.is_token_blacklisted(jti, user_id)
        
        if is_blacklisted:
            current_app.logger.info(f"Blocked blacklisted token {jti} for user {user_id}")
        
        return is_blacklisted

class UserController:
    """
    Controller for user operations
    """
    
    @staticmethod
    def get_all_users():
        """
        Get all users
        """
        try:
            users = User.query.all()
            users_list = [user.to_dict() for user in users]
            return users_list, None
        except Exception as e:
            current_app.logger.error(f"Error fetching users: {str(e)}")
            return [], f"Error fetching users: {str(e)}"
    
    @staticmethod
    def login_user(email, password):
        """
        Login a user with email and password
        """
        try:
            logging.info(f"Login attempt - email: {email}, password length: {len(password) if password else 0}")
            
            if not email or not password:
                logging.warning("Missing email or password")
                return None, "Email and password are required"
            
            # Sanitize email
            original_email = email
            email = sanitize_input(email)
            logging.info(f"Email after sanitization: {original_email} -> {email}")
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            logging.info(f"User found: {user is not None}")
            
            if not user:
                logging.warning(f"No user found with email: {email}")
                return None, "Invalid email or password"
            
            # Check password
            password_valid = user.check_password(password)
            logging.info(f"Password check result: {password_valid}")
            
            if not password_valid:
                logging.warning(f"Password validation failed for user: {email}")
                return None, "Invalid email or password"
            
            logging.info(f"Login successful for user: {email}")
            return user, None
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            return None, f"Login error: {str(e)}"
    
    @staticmethod
    def register_user(user_data):
        """
        Register a new user
        """
        try:
            # Extract and sanitize user data
            email = sanitize_input(user_data.get('email', ''))
            username = sanitize_input(user_data.get('username', ''))
            password = user_data.get('password', '')  # Don't sanitize password
            
            # Validate required fields
            if not email or not username or not password:
                return None, "Email, username and password are required"
            
            # Validate email format
            if not validate_email(email):
                return None, "Invalid email format"
            
            # Check if email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return None, "Email already exists"
            
            # Validate password strength
            if len(password) < 8:
                return None, "Password must be at least 8 characters long"
            
            # Create user
            user = User(
                email=email,
                username=username,
                is_admin=False
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            logging.info(f"User registered: {user.username} ({user.email})")
            return user, None
        except Exception as e:
            current_app.logger.error(f"Registration error: {str(e)}")
            db.session.rollback()
            return None, f"Registration error: {str(e)}"
    
    @staticmethod
    def update_user_data(user_id, data):
        """
        Update user data (username, email)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            update_needed = False
            
            # Update username if provided
            if 'username' in data and data['username']:
                username = sanitize_input(data['username'])
                if username and user.username != username:
                    user.username = username
                    update_needed = True
            
            # Update email if provided
            if 'email' in data and data['email']:
                email = sanitize_input(data['email'])
                if email and user.email != email:
                    # Validate email format
                    if not validate_email(email):
                        return None, "Invalid email format"
                    
                    # Check if email is already in use
                    existing_user = User.query.filter_by(email=email).first()
                    if existing_user and existing_user.id != user_id:
                        return None, "Email already in use"
                    
                    user.email = email
                    update_needed = True
            
            if update_needed:
                db.session.commit()
            
            return user.to_dict(), None
        except Exception as e:
            current_app.logger.error(f"User update error: {str(e)}")
            db.session.rollback()
            return None, f"User update error: {str(e)}"
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """
        Change user password
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            # Check current password
            if not user.check_password(current_password):
                return None, "Invalid current password"
            
            # Validate new password
            if len(new_password) < 8:
                return None, "Password must be at least 8 characters long"
            
            # Set new password
            user.set_password(new_password)
            db.session.commit()
            
            return {"message": "Password changed successfully"}, None
        except Exception as e:
            current_app.logger.error(f"Password change error: {str(e)}")
            db.session.rollback()
            return None, f"Password change error: {str(e)}"
    
    @staticmethod
    def update_user_avatar(user_id, avatar_url):
        """
        Update user avatar
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            # Update avatar
            user.avatar_url = avatar_url
            db.session.commit()
            
            return {"message": "Avatar updated successfully"}, None
        except Exception as e:
            current_app.logger.error(f"Avatar update error: {str(e)}")
            db.session.rollback()
            return None, f"Avatar update error: {str(e)}"
