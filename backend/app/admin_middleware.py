"""
Admin middleware for role-based access control
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import User

def admin_required(f):
    """Decorator that requires admin role"""
    @wraps(f)
    @jwt_required(locations=["cookies"])
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            user = User.query.get(current_user_id)
            # If user not found by ID, try by google_id (for OAuth users)
            if not user:
                user = User.query.filter_by(google_id=current_user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not user.is_admin_user():
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

def moderator_or_admin_required(f):
    """Decorator that requires moderator or admin role"""
    @wraps(f)
    @jwt_required(locations=["cookies"])
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            user = User.query.get(current_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not (user.has_role('admin') or user.has_role('moderator')):
                return jsonify({'error': 'Moderator or admin access required'}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

def get_current_admin_user():
    """Get current admin user from JWT token"""
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return None
        
        user = User.query.get(current_user_id)
        if user and user.is_admin_user():
            return user
        return None
    except:
        return None
