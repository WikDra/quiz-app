"""
Pomocnicze funkcje dla aplikacji
"""
import json
import os
import re
import secrets
import base64
from pathlib import Path
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

def load_json_data(file_path):
    """Wczytuje dane z pliku JSON, obsługując komentarze na początku pliku"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Usuń komentarz z początku pliku jeśli istnieje
        if content.strip().startswith('//'):
            content = '\n'.join(content.splitlines()[1:])
            
        return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Błąd odczytu pliku {file_path}: {e}")
        return None
        
def generate_secure_key(bytes_length=32):
    """Generuje bezpieczny klucz kryptograficzny"""
    return base64.urlsafe_b64encode(secrets.token_bytes(bytes_length)).decode('utf-8')

def sanitize_input(text):
    """Podstawowa sanityzacja danych wejściowych"""
    if text is None:
        return None
    # Usuń potencjalnie niebezpieczne znaki i sekwencje
    sanitized = re.sub(r'[<>()\\&;]', '', str(text))
    return sanitized

def validate_email(email):
    """Sprawdza poprawność adresu email"""
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$'
    return bool(re.match(pattern, email))

def admin_required(func):
    """Dekorator wymagający administratora"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            from models.user import User  # Import tutaj, aby uniknąć importowania cyklicznego
            
            user = User.query.get(user_id)
            if not user or not user.is_admin:
                return jsonify({"error": "Admin access required"}), 403
                
            return func(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Authorization error: {str(e)}")
            return jsonify({"error": "Access denied"}), 401
    return wrapper

def is_strong_password(password):
    """
    Sprawdza czy hasło jest wystarczająco silne.
    Hasło musi mieć co najmniej 8 znaków i zawierać:
    - przynajmniej jedną wielką literę
    - przynajmniej jedną małą literę
    - przynajmniej jedną cyfrę
    - przynajmniej jeden znak specjalny
    """
    if not password or len(password) < 8:
        return False, "Hasło musi mieć co najmniej 8 znaków"
    
    if not re.search(r'[A-Z]', password):
        return False, "Hasło musi zawierać co najmniej jedną wielką literę"
    
    if not re.search(r'[a-z]', password):
        return False, "Hasło musi zawierać co najmniej jedną małą literę"
    
    if not re.search(r'[0-9]', password):
        return False, "Hasło musi zawierać co najmniej jedną cyfrę"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Hasło musi zawierać co najmniej jeden znak specjalny"
    
    return True, "Hasło jest wystarczająco silne"
