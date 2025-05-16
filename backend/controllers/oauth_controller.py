"""
Kontroler do obsługi autoryzacji OAuth2 (Google)
"""
import os
import json
from datetime import datetime
from flask import url_for, current_app, redirect, request, session
from authlib.integrations.flask_client import OAuth
import requests

import sys
import os

# Append parent directory to path for imports
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if module_path not in sys.path:
    sys.path.insert(0, module_path)

from __init__ import db
from models.user import User
from utils.helpers import sanitize_input, validate_email

# Inicjalizacja OAuth
oauth = OAuth()

def init_oauth(app):
    """
    Inicjalizuje obsługę OAuth dla aplikacji Flask.
    Należy wywołać tę funkcję w czasie konfiguracji aplikacji.
    """    # Pobierz dane konfiguracyjne Google OAuth z zmiennych środowiskowych
    # W rozwoju można użyć wartości testowych, ale w produkcji powinny być ustawione w zmiennych środowiskowych
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    if not google_client_id or not google_client_secret:
        app.logger.error("Google OAuth credentials not set in environment variables. Google login will not work.")
        app.logger.error("Please run 'python backend/utils/setup_security.py' to configure OAuth properly.")
    
    oauth.init_app(app)
    
    # Rejestracja Google jako dostawcy OAuth
    oauth.register(
        name='google',
        client_id=google_client_id,
        client_secret=google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    return oauth

class OAuthController:
    @staticmethod
    def login_with_google():
        """
        Inicjuje proces logowania z użyciem Google OAuth.
        """
        if not oauth.google.client_id:
            current_app.logger.error("Google OAuth nie skonfigurowany - brak client_id.")
            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
            return redirect(f'{frontend_url}/login?error=GoogleOAuthNotConfigured')
            
        # Zapisz URL przekierowania po autoryzacji
        redirect_uri = url_for('authorize_google', _external=True)
        current_app.logger.info(f"Przekierowuję do Google OAuth z redirect_uri: {redirect_uri}")
        return oauth.google.authorize_redirect(redirect_uri)
    
    @staticmethod
    def handle_google_callback():
        """
        Obsługuje odpowiedź z serwera autoryzującego Google.
        """
        try:
            token = oauth.google.authorize_access_token()
            if not token:
                return None, "Authorization failed"
            
            # Pobierz informacje o użytkowniku
            userinfo = token.get('userinfo')
            if not userinfo:
                # Jeśli nie ma userinfo w tokenie, pobierz je przez API
                resp = oauth.google.get('userinfo')
                if resp.status_code != 200:
                    return None, f"Failed to get user info: {resp.text}"
                userinfo = resp.json()
              # Informacje o użytkowniku z Google - sanityzacja danych
            google_id = sanitize_input(userinfo.get('sub'))
            email = sanitize_input(userinfo.get('email'))
            full_name = sanitize_input(userinfo.get('name'))
            avatar_url = sanitize_input(userinfo.get('picture'))  # Pobranie URL zdjęcia profilowego
            
            # Walidacja podstawowych danych
            if not google_id or not email:
                current_app.logger.warning("OAuth callback otrzymał niepełne dane od Google")
                return None, "Invalid user information received from Google"
                
            # Dodatkowa walidacja emaila
            if not validate_email(email):
                current_app.logger.warning(f"OAuth callback otrzymał niepoprawny format emaila: {email}")
                return None, "Invalid email format received from OAuth provider"
            
            # Sprawdź czy użytkownik już istnieje w bazie danych (według adresu email lub social_id)
            user = User.query.filter(
                (User.email == email) | 
                ((User.social_id == google_id) & (User.social_provider == 'google'))
            ).first()
            
            if not user:                # Dodatkowa walidacja przed utworzeniem użytkownika
                if not full_name or len(full_name.strip()) < 1:
                    # Jeśli nie ma pełnej nazwy, użyj części emaila jako nazwy
                    full_name = email.split('@')[0]
                    current_app.logger.warning(f"Brak pełnej nazwy z Google, używam części email: {full_name}")
                
                # Utwórz nowego użytkownika z sanityzowanymi danymi
                user = User(
                    username=full_name,
                    email=email,
                    social_id=google_id,
                    social_provider='google',
                    avatar_url=avatar_url,
                    is_admin=False  # Nowi użytkownicy z OAuth nie są adminami
                )
                
                # Ustaw silne losowe hasło, które nie będzie używane (użytkownik loguje się przez Google)
                from utils.helpers import generate_secure_key
                random_password = generate_secure_key(32)  # 32 bajty losowych danych
                user.set_password(random_password)
                
                db.session.add(user)
                db.session.commit()
                current_app.logger.info(f"Created new user via Google OAuth: {email}")
                return user, None
            else:
                # Aktualizuj informacje o istniejącym użytkowniku
                update_needed = False
                
                # Jeśli to pierwszy login przez Google dla istniejącego konta
                if not user.social_id or not user.social_provider == 'google':
                    user.social_id = google_id
                    user.social_provider = 'google'
                    update_needed = True
                
                # Aktualizuj awatar, jeśli jest dostępny
                if avatar_url and user.avatar_url != avatar_url:
                    user.avatar_url = avatar_url
                    update_needed = True
                
                # Aktualizuj nazwę użytkownika, jeśli jest niekompletna
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
