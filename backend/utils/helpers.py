"""
Helper functions for the application
"""
import os
import re
import base64
import secrets
from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from app.models import User

def sanitize_input(input_str):
    """
    Sanitize input string to prevent XSS
    """
    if input_str is None:
        return None
    
    # Convert to string if not already
    if not isinstance(input_str, str):
        input_str = str(input_str)
    
    # Sanitize by replacing problematic characters
    sanitized = input_str.strip()
    sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<.*?>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized

def validate_email(email):
    """
    Validate email format
    """
    if not email:
        return False
    
    # Simple regex for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def admin_required(fn):
    """
    Decorator to check if user is admin
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Check if user exists and is admin
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def generate_secure_key(length=32):
    """
    Generate a secure random key
    """
    return base64.b64encode(secrets.token_bytes(length))
