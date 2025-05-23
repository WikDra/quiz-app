from flask import Blueprint, request, jsonify, session, make_response, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import generate_csrf, validate_csrf
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from werkzeug.security import check_password_hash
import requests
from datetime import datetime

from app import oauth, init_oauth
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

def log_auth_debug(message, data=None):
    """Helper to log authentication related debug info"""
    if data is None:
        data = {}
    current_app.logger.debug(f"AUTH DEBUG - {message}: {data}")

# Helper function to get OAuth client
def get_google_client():
    if not hasattr(oauth, 'google'):
        oauth.register(
            name='google',
            client_id=current_app.config['GOOGLE_CLIENT_ID'],
            client_secret=current_app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
    return oauth.google

# Forms for validation
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    first_name = StringField('First Name', validators=[Length(max=50)])
    last_name = StringField('Last Name', validators=[Length(max=50)])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ta nazwa użytkownika jest już zajęta.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ten email jest już zarejestrowany.')

@auth_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    """Get CSRF token for frontend"""
    token = generate_csrf()
    response = make_response(jsonify({'csrf_token': token}))
    
    # Set CSRF cookie explicitly
    response.set_cookie(
        'csrf_token',
        token,
        secure=current_app.config['SESSION_COOKIE_SECURE'],
        httponly=False,  # Frontend needs to read this
        samesite=current_app.config['SESSION_COOKIE_SAMESITE'],
        max_age=None  # Session cookie
    )
    
    return response

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        form = RegisterForm()
        
        if not form.validate_on_submit():
            return jsonify({
                'success': False,
                'message': 'Błędne dane',
                'errors': form.errors
            }), 400
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Log in the new user
        login_user(user, remember=True)
        user.update_last_login()
        
        return jsonify({
            'success': True,
            'message': 'Konto zostało utworzone i zostałeś zalogowany',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas rejestracji: {str(e)}'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        form = LoginForm()
        
        if not form.validate_on_submit():
            return jsonify({
                'success': False,
                'message': 'Błędne dane',
                'errors': form.errors
            }), 400
        
        # Find user
        user = User.query.filter_by(email=form.email.data).first()
        
        if not user or not user.check_password(form.password.data):
            return jsonify({
                'success': False,
                'message': 'Nieprawidłowy email lub hasło'
            }), 401
        
        # Log in user
        login_user(user, remember=form.remember_me.data)
        user.update_last_login()
        
        # Create response with proper session cookie
        response = make_response(jsonify({
            'success': True,
            'message': 'Pomyślnie zalogowano',
            'user': user.to_dict()
        }))
        
        # Ensure session cookie is set properly
        session.permanent = True
        
        # Set explicit session cookie attributes
        response.set_cookie(
            'session', 
            session.sid if hasattr(session, 'sid') else request.cookies.get('session', ''),
            max_age=3600 * 24 * 7,  # 7 days
            path='/',
            secure=False,  # Set to True in production
            httponly=True,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Błąd podczas logowania: {str(e)}'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    try:
        logout_user()
        session.clear()
        
        response = make_response(jsonify({
            'success': True,
            'message': 'Pomyślnie wylogowano'
        }))
        
        # Clear remember me cookie
        response.set_cookie('remember_token', '', expires=0)
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas wylogowywania: {str(e)}'
        }), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    try:
        log_auth_debug("Checking auth state", {
            'session_keys': list(session.keys()) if session else [],
            'has_current_user': bool(current_user),
            'current_user_attrs': dir(current_user) if hasattr(current_user, '__dict__') else None
        })

        has_session = bool(session.get('user_id')) and bool(session.get('_fresh'))
        
        # Call is_authenticated method if it's a method
        if hasattr(current_user, 'is_authenticated'):
            if callable(current_user.is_authenticated):
                is_authenticated = current_user.is_authenticated()
            else:
                is_authenticated = current_user.is_authenticated
        else:
            is_authenticated = False

        log_auth_debug("Auth state checked", {
            'has_session': has_session,
            'is_authenticated': is_authenticated
        })

        user_data = None
        if is_authenticated and hasattr(current_user, 'to_dict'):
            try:
                user_data = current_user.to_dict()
            except Exception as e:
                current_app.logger.error(f"Error serializing user data: {e}")
                log_auth_debug("User serialization failed", {'error': str(e)})

        # Create response
        response = make_response(jsonify({
            'success': True,
            'authenticated': is_authenticated,
            'hasSession': has_session,
            'user': user_data
        }))
        
        # If authenticated, ensure session cookie is set
        if is_authenticated:
            # Ensure the session is marked permanent
            session.permanent = True
            
            # Only set cookie if session ID exists
            if '_id' in session:
                response.set_cookie(
                    'session', 
                    session.get('_id', ''),
                    max_age=3600 * 24 * 7,  # 7 days
                    path='/',
                    secure=False,  # Set to True in production
                    httponly=True,
                    samesite='Lax'
                )
        
        return response
    except Exception as e:
        current_app.logger.error(f"Error in check_auth: {e}")
        log_auth_debug("Check auth failed", {'error': str(e)})
        return jsonify({
            'success': False,
            'message': 'Error checking authentication status',
            'authenticated': False,
            'hasSession': False,
            'user': None
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh user session with CSRF validation"""
    try:
        # Debug logging
        log_auth_debug("Refresh endpoint called", {
            'method': request.method,
            'headers': dict(request.headers),
            'is_json': request.is_json,
            'json_data': request.get_json(silent=True),
            'form_data': request.form,
            'is_authenticated': getattr(current_user, 'is_authenticated', False),
            'session': dict(session)
        })
        
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token and request.is_json:
            csrf_token = request.json.get('csrf_token')
            
        log_auth_debug("CSRF validation", {
            'token_from_header': request.headers.get('X-CSRFToken'),
            'token_from_json': request.get_json(silent=True).get('csrf_token') if request.is_json else None,
            'request_json': request.get_json(silent=True)
        })
        
        try:
            validate_csrf(csrf_token)
        except ValidationError:
            log_auth_debug("CSRF validation failed", {'token': csrf_token})
            return jsonify({
                'success': False,
                'message': 'CSRF validation failed'
            }), 400

            validate_csrf(csrf_token)
            log_auth_debug("CSRF validation successful")
        except Exception as e:
            log_auth_debug("CSRF validation failed", {
                'error': str(e),
                'error_type': type(e).__name__,
                'token': csrf_token
            })
            return jsonify({
                'success': False,
                'message': f'Invalid CSRF token: {str(e)}'
            }), 400

        # Authentication check
        if not current_user.is_authenticated:
            log_auth_debug("User not authenticated")
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401

        # Update last login time
        current_user.update_last_login()
        
        # Create response with proper session cookie
        response = make_response(jsonify({
            'success': True,
            'message': 'Session refreshed successfully',
            'user': current_user.to_dict()
        }))
        
        # Ensure session is marked as permanent
        session.permanent = True
        
        # Set proper session cookie
        if '_id' in session:
            response.set_cookie(
                'session',
                session.get('_id', ''),
                max_age=3600 * 24 * 7,  # 7 days
                path='/',
                secure=False,  # Set to True in production
                httponly=True,
                samesite='Lax'
            )

        # Debug cookie for client-side verification
        response.set_cookie(
            'session_debug',
            f"refreshed_at={datetime.utcnow().isoformat()}|user:{current_user.id}",
            max_age=3600,
            path='/',
            secure=False,
            httponly=False,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error in refresh endpoint: {e}")
        log_auth_debug("Refresh failed", {'error': str(e)})
        return jsonify({
            'success': False,
            'message': f'Error refreshing session: {str(e)}'
        }), 500

@auth_bp.route('/set-session', methods=['GET'])
def set_session_cookie():
    """Explicitly set session cookie for debugging"""
    try:
        # Check if user is authenticated
        is_authenticated = current_user.is_authenticated if hasattr(current_user, 'is_authenticated') and callable(current_user.is_authenticated) else bool(getattr(current_user, 'is_authenticated', False))
        
        if not is_authenticated:
            return jsonify({
                'success': False,
                'message': 'User not authenticated',
                'cookie_set': False
            })
        
        # Generate session response
        response = make_response(jsonify({
            'success': True,
            'message': 'Session cookie set',
            'cookie_set': True,
            'session_id': session.get('_id', ''),
            'user_id': current_user.id if is_authenticated else None,
            'session_keys': list(session.keys())
        }))
        
        # Force set session cookie with SameSite=None for cross-site testing
        session_id = session.get('_id', '')
        if session_id:
            # Keep the real session cookie as HttpOnly for security
            response.set_cookie(
                'session',
                session_id,
                max_age=3600 * 24 * 7,  # 7 days
                path='/',
                secure=False,  # Should be True in production
                httponly=True,
                samesite='Lax'
            )
            
            # Set a visible cookie for client-side detection
            response.set_cookie(
                'visible_session',
                'true',
                max_age=3600 * 24 * 7,
                path='/',
                secure=False,
                httponly=False,
                samesite='Lax'
            )
            
            # Add session-related info as a visible cookie for debugging
            response.set_cookie(
                'session_debug',
                f"user:{current_user.id}|authenticated:{is_authenticated}",
                max_age=3600 * 24 * 7,
                path='/',
                secure=False,
                httponly=False,
                samesite='Lax'
            )
        
        return response
    except Exception as e:
        current_app.logger.error(f"Error setting session cookie: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'cookie_set': False
        }), 500

@auth_bp.route('/debug', methods=['GET'])
def debug_auth():
    """Debug endpoint to get auth info"""
    try:
        # Print session info for debugging
        current_app.logger.debug(f"Session data: {session}")
        current_app.logger.debug(f"Cookies: {request.cookies}")
        
        # Get session cookie from request
        session_cookie = request.cookies.get('session', '')
        
        # Log the session ID
        session_id = session.get('_id', '')
        current_app.logger.debug(f"Session ID: {session_id}")
        
        # Get cookie details
        all_cookies = {k: v[:10] + '...' if len(v) > 10 else v for k, v in request.cookies.items()}
        
        return jsonify({
            'success': True,
            'authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') and callable(current_user.is_authenticated) else bool(getattr(current_user, 'is_authenticated', False)),
            'user': current_user.to_dict() if hasattr(current_user, 'to_dict') else None,
            'session_data': {
                'has_session': '_user_id' in session,
                'fresh': session.get('_fresh', False),
                'session_id': session.get('_id'),
                'user_id': session.get('_user_id'),
                'csrf_token': bool(session.get('csrf_token')),
                'keys': list(session.keys())
            },
            'cookies_count': len(request.cookies),
            'cookies': all_cookies,
            'session_cookie_present': 'session' in request.cookies,
            'session_cookie_length': len(session_cookie) if session_cookie else 0,
            'session_valid': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False,
            'flask_session_cookie_name': current_app.config.get('SESSION_COOKIE_NAME', 'session')
        })
    except Exception as e:
        current_app.logger.error(f"Error in debug_auth: {e}")
        return jsonify({
            'success': False,
            'message': 'Error checking auth state',
            'error': str(e)
        }), 500

@auth_bp.route('/ping', methods=['GET'])
def ping_auth():
    """Simple ping endpoint to check auth status and initialize session"""
    try:
        # Just reading the session will initialize it if needed
        has_session = '_user_id' in session
        is_authenticated = current_user.is_authenticated if hasattr(current_user, 'is_authenticated') and callable(current_user.is_authenticated) else bool(getattr(current_user, 'is_authenticated', False))
        
        # Create a response
        response = make_response(jsonify({
            'success': True,
            'authenticated': is_authenticated,
            'hasSession': has_session,
            'time': datetime.utcnow().isoformat()
        }))
        
        return response
    except Exception as e:
        current_app.logger.error(f"Error in ping_auth: {e}")
        return jsonify({
            'success': False,
            'message': 'Error pinging auth',
            'error': str(e)
        }), 500

# Google OAuth routes
@auth_bp.route('/google', methods=['GET'])
def google_login():
    """Redirect to Google OAuth"""
    try:
        # Check if Google OAuth is configured
        if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
            return jsonify({
                'success': False,
                'message': 'Google OAuth nie jest skonfigurowany. Skontaktuj się z administratorem.'            
                }), 503        # Get Google OAuth client
        google = get_google_client()
        
        # Generate redirect URI
        redirect_uri = url_for('auth.google_callback', _external=True)
        
        # Redirect to Google for authorization
        return google.authorize_redirect(redirect_uri)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas inicjalizacji Google OAuth: {str(e)}'
        }), 500

@auth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """Handle Google OAuth callback"""
    try:        # Check if Google OAuth is configured
        if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
            # Redirect to frontend with error
            frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
            return redirect(f"{frontend_url}/login?error=oauth_not_configured")
          # Get Google OAuth client
        google = get_google_client()
        
        # Get token from Google
        token = google.authorize_access_token()
        
        # Get user info from token or API
        user_info = token.get('userinfo')
        if not user_info:
            # If userinfo not in token, get it from API
            resp = google.get('userinfo')
            if resp.ok:
                user_info = resp.json()
            else:
                current_app.logger.error(f"Failed to get user info: {resp.text}")
        
        if not user_info:
            # Redirect to frontend with error            
            frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
            return redirect(f"{frontend_url}/login?error=oauth_failed")
        
        # Check if user exists
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            # Create new user from Google data
            user = User(
                username=user_info.get('given_name', user_info['email'].split('@')[0]),
                email=user_info['email'],
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
                google_id=user_info.get('sub'),
                is_oauth_user=True
            )
            # Set a random password (user won't need it for Google auth)
            user.set_password('google_oauth_user_no_password')
            
            db.session.add(user)
            db.session.commit()
        
        # Log in the user
        login_user(user, remember=True)
        user.update_last_login()
        
        # Redirect to frontend home page
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
        return redirect(f"{frontend_url}/home")
        
    except Exception as e:
        # Redirect to frontend with error
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
        return redirect(f"{frontend_url}/login?error=oauth_error")
