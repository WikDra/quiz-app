from functools import wraps
from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def rate_limit_by_user():
    """Custom rate limiting by user ID if authenticated, otherwise by IP"""
    from flask_login import current_user
    if current_user.is_authenticated:
        return f"user_{current_user.id}"
    return get_remote_address()

def handle_rate_limit_exceeded(e):
    """Custom rate limit exceeded handler"""
    return jsonify({
        'success': False,
        'message': 'Przekroczono limit żądań. Spróbuj ponownie później.',
        'retry_after': e.retry_after
    }), 429
