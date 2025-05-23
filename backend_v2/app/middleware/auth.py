from functools import wraps
from flask import jsonify
from flask_login import current_user

def premium_required(f):
    """Decorator to require premium subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'Wymagane logowanie'
            }), 401
        
        if not current_user.is_premium:
            return jsonify({
                'success': False,
                'message': 'Ta funkcja wymaga konta Premium',
                'premium_required': True
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role (for future use)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'Wymagane logowanie'
            }), 401
        
        # For now, check if user is admin by email or add admin field to User model
        admin_emails = ['admin@quiz-app.com']  # Add admin emails here
        if current_user.email not in admin_emails:
            return jsonify({
                'success': False,
                'message': 'Brak uprawnień administratora'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function
