"""BlacklistedToken model definition."""

from ..extensions import db
from datetime import datetime


class BlacklistedToken(db.Model):
    """
    Model for storing blacklisted JWT tokens to prevent their reuse after logout
    """
    __tablename__ = 'blacklisted_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)  # JWT ID (unique identifier)
    token_type = db.Column(db.String(10), nullable=False)  # 'access' or 'refresh'
    user_id = db.Column(db.String(100), nullable=False)  # Changed to String to handle large OAuth IDs
    revoked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)  # When the token would naturally expire
    
    def __init__(self, jti, token_type, user_id, expires_at):
        self.jti = jti
        self.token_type = token_type
        self.user_id = user_id
        self.expires_at = expires_at
    
    def __repr__(self):
        return f'<BlacklistedToken {self.jti}>'
    
    @staticmethod
    def is_blacklisted(jti):
        """Check if a token is blacklisted"""
        return BlacklistedToken.query.filter_by(jti=jti).first() is not None
    
    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired blacklisted tokens from database"""
        expired_tokens = BlacklistedToken.query.filter(
            BlacklistedToken.expires_at < datetime.utcnow()
        ).all()
        
        for token in expired_tokens:
            db.session.delete(token)
        
        db.session.commit()
        return len(expired_tokens)

    def to_dict(self):
        return {
            'id': self.id,
            'jti': self.jti,
            'token_type': self.token_type,
            'user_id': self.user_id,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
