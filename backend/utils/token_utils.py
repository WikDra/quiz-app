"""
Utility functions for JWT token management
"""
from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import get_jwt, create_refresh_token
from models import db
from models.user import InvalidToken
import random

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

def invalidate_token(token_claims):
    """
    Add a token to the blacklist.
    
    Args:
        token_claims (dict): Claims from the token to invalidate.
        
    Returns:
        InvalidToken: The created InvalidToken record.
    """
    jti = token_claims.get('jti')
    expires = datetime.fromtimestamp(token_claims.get('exp'))
    user_id = int(token_claims.get('sub'))
    token_type = token_claims.get('type', 'access')
    
    invalid_token = InvalidToken(
        jti=jti,
        type=token_type,
        user_id=user_id,
        expires=expires
    )
    db.session.add(invalid_token)
    db.session.commit()
    
    return invalid_token

def create_rotated_refresh_token(identity, old_token_claims):
    """
    Create a new refresh token while invalidating the old one.
    
    Args:
        identity (str): User identity for the new token.
        old_token_claims (dict): Claims from the old token to rotate.
        
    Returns:
        str: New refresh token
    """
    # Get refresh count from old token
    old_refresh_count = old_token_claims.get('refresh_count', 0)
    
    # Create new token with incremented refresh count
    new_token = create_refresh_token(
        identity=identity,
        additional_claims={
            'refresh_count': old_refresh_count + 1,
            'type': 'refresh',
            'rotated_at': datetime.utcnow().isoformat()
        }
    )
    
    # Invalidate the old token
    invalidate_token(old_token_claims)
    
    return new_token

def maybe_cleanup_tokens():
    """
    Attempt to clean up expired tokens, but only occasionally to prevent
    too frequent database operations. Should be called on token refresh.
    """
    try:
        # Only run cleanup ~5% of the time when this function is called
        if random.random() < 0.05:
            cleanup_expired_tokens()
    except Exception as e:
        current_app.logger.error(f"Error in token cleanup: {str(e)}")

def cleanup_expired_tokens():
    """
    Remove expired tokens from the invalid_tokens table.
    Should be called periodically to prevent the table from growing too large.
    """
    try:
        now = datetime.utcnow()
        expired_count = InvalidToken.query.filter(InvalidToken.expires < now).delete()
        db.session.commit()
        current_app.logger.info(f"Cleaned up {expired_count} expired tokens from blacklist")
        return expired_count
    except Exception as e:
        current_app.logger.error(f"Error cleaning up expired tokens: {str(e)}")
        db.session.rollback()
        return 0
