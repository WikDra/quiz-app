"""
OAuth controller for Google authentication
"""
import os
import sys
from flask import url_for, current_app, redirect, request
from authlib.integrations.flask_client import OAuth
from models import db
from models.user import User
from utils.helpers import sanitize_input, validate_email, generate_secure_key

# Initialize OAuth
oauth = OAuth()
oauth_initialized = False

def init_oauth(app):
    """
    Initialize OAuth handling for Flask application
    """
    global oauth, oauth_initialized
    
    # Check if OAuth is already initialized
    if oauth_initialized:
        app.logger.info("OAuth already initialized, skipping...")
        return oauth
    
    # Get Google OAuth config from environment variables
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    if not google_client_id or not google_client_secret:
        app.logger.error("Google OAuth credentials not set in environment variables")
        app.logger.error("Please check your .env file or run setup_security.py")
    
    # Initialize OAuth with the app
    oauth.init_app(app)
    
    # Register Google as an OAuth provider
    oauth.register(
        name='google',
        client_id=google_client_id,
        client_secret=google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    oauth_initialized = True
    app.logger.info("OAuth initialized successfully with Google provider")
    
    return oauth

class OAuthController:
    """
    Controller for OAuth operations
    """
    
    @staticmethod
    def login_with_google():
        """
        Initiate Google OAuth login process
        """
        global oauth, oauth_initialized
        
        try:
            # Check if Google client is registered
            if not oauth_initialized or not hasattr(oauth, 'google'):
                current_app.logger.error("Google OAuth not configured - missing client_id or initialization")
                frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
                return redirect(f'{frontend_url}/login?error=GoogleOAuthNotConfigured')
                
            # Set redirect URI after authorization
            redirect_uri = url_for('authorize_google', _external=True)
            current_app.logger.info(f"Redirecting to Google OAuth with redirect_uri: {redirect_uri}")
            return oauth.google.authorize_redirect(redirect_uri)
        except AttributeError as e:
            current_app.logger.error(f"Google OAuth not configured - error: {str(e)}")
            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
            return redirect(f'{frontend_url}/login?error=GoogleOAuthNotConfigured')
    
    @staticmethod
    def handle_google_callback():
        """
        Handle response from Google authorization server
        """
        try:
            token = oauth.google.authorize_access_token()
            if not token:
                return None, "Authorization failed"
            
            # Get user information
            userinfo = token.get('userinfo')
            if not userinfo:
                # If userinfo not in token, get it from API
                resp = oauth.google.get('userinfo')
                if resp.status_code != 200:
                    return None, f"Failed to get user info: {resp.text}"
                userinfo = resp.json()
            
            # Sanitize user data
            google_id = sanitize_input(userinfo.get('sub'))
            email = sanitize_input(userinfo.get('email'))
            full_name = sanitize_input(userinfo.get('name'))
            avatar_url = sanitize_input(userinfo.get('picture'))
            
            # Basic validation
            if not google_id or not email:
                current_app.logger.warning("OAuth callback received incomplete data from Google")
                return None, "Invalid user information received from Google"
                
            # Email validation
            if not validate_email(email):
                current_app.logger.warning(f"OAuth callback received invalid email format: {email}")
                return None, "Invalid email format received from OAuth provider"
            
            # Check if user exists
            user = User.query.filter(
                (User.email == email) | 
                ((User.social_id == google_id) & (User.social_provider == 'google'))
            ).first()
            
            if not user:
                # Create new user if not exists
                if not full_name or len(full_name.strip()) < 1:
                    # If no full name, use part of email as name
                    full_name = email.split('@')[0]
                    current_app.logger.warning(f"No full name from Google, using email part: {full_name}")
                
                # Create new user
                user = User(
                    username=full_name,
                    email=email,
                    social_id=google_id,
                    social_provider='google',
                    avatar_url=avatar_url,
                    is_admin=False
                )
                
                # Set random password (not used as user logs in with Google)
                random_password = generate_secure_key(32)
                user.set_password(random_password)
                
                db.session.add(user)
                db.session.commit()
                current_app.logger.info(f"Created new user via Google OAuth: {email}")
                return user, None
            else:
                # Update existing user information
                update_needed = False
                
                # First Google login for existing account
                if not user.social_id or not user.social_provider == 'google':
                    user.social_id = google_id
                    user.social_provider = 'google'
                    update_needed = True
                
                # Update avatar if available
                if avatar_url and user.avatar_url != avatar_url:
                    user.avatar_url = avatar_url
                    update_needed = True
                
                # Update username if incomplete
                if full_name and (not user.username or len(user.username) < 2):
                    user.username = full_name
                    update_needed = True
                
                if update_needed:
                    db.session.commit()
                    current_app.logger.info(f"Updated user info via Google OAuth: {email}")
                return user, None
        except Exception as e:
            current_app.logger.error(f"Google OAuth error: {str(e)}")
            return None, f"Authentication error: {str(e)}"
