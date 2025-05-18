"""
Controller for user management
"""
import re
from flask import current_app
from models import db
from models.user import User
from utils.helpers import sanitize_input, validate_email

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
            if not email or not password:
                return None, "Email and password are required"
            
            # Sanitize email
            email = sanitize_input(email)
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return None, "Invalid email or password"
            
            # Check password
            if not user.check_password(password):
                return None, "Invalid email or password"
            
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
