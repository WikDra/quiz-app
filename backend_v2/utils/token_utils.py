"""
Utility functions for JWT token management
"""
from datetime import datetime, timedelta
from flask_jwt_extended import get_jwt
from flask import current_app

def check_token_expiration(token_claims=None, buffer_time=300):
    """
    Check if a token is nearing expiration.
    
    Args:
        token_claims (dict, optional): Claims from the token. If None, gets current token claims.
        buffer_time (int): Number of seconds before expiration to consider token as expiring.
        
    Returns:
        tuple: (is_expiring, seconds_until_expiry)
    """
    if token_claims is None:
        token_claims = get_jwt()
    
    exp_timestamp = token_claims.get('exp', 0)
    current_timestamp = datetime.utcnow().timestamp()
    time_until_expiry = exp_timestamp - current_timestamp
    
    return time_until_expiry <= buffer_time, time_until_expiry

def should_rotate_refresh_token(token_claims=None, rotation_threshold=24*3600):
    """
    Determine if refresh token should be rotated based on expiration and usage.
    
    Args:
        token_claims (dict, optional): Claims from the refresh token.
        rotation_threshold (int): Time in seconds before expiration to trigger rotation.
        
    Returns:
        bool: True if token should be rotated
    """
    if token_claims is None:
        token_claims = get_jwt()
    
    is_expiring, time_until_expiry = check_token_expiration(token_claims)
    refresh_count = token_claims.get('refresh_count', 0)
    max_refresh_count = current_app.config.get('JWT_MAX_REFRESH_COUNT', 100)
    
    # Rotate if:
    # 1. Token is nearing expiration (less than threshold seconds left)
    # 2. Token has been refreshed too many times
    # 3. Token is older than half its maximum lifetime
    return (
        time_until_expiry < rotation_threshold or
        refresh_count >= max_refresh_count or
        time_until_expiry < current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds() / 2
    )

def get_token_metadata():
    """
    Get metadata about the current token.
    
    Returns:
        dict: Token metadata including expiration, age, refresh count, etc.
    """
    token_claims = get_jwt()
    exp_timestamp = token_claims.get('exp', 0)
    iat_timestamp = token_claims.get('iat', 0)
    current_timestamp = datetime.utcnow().timestamp()
    
    return {
        'token_type': token_claims.get('type'),
        'refresh_count': token_claims.get('refresh_count', 0),
        'time_until_expiry': exp_timestamp - current_timestamp,
        'token_age': current_timestamp - iat_timestamp,
        'is_expiring': check_token_expiration(token_claims)[0],
        'should_rotate': should_rotate_refresh_token(token_claims),
        'jti': token_claims.get('jti'),  # Unique token identifier
        'user_id': token_claims.get('sub')  # Subject (user ID)
    }
