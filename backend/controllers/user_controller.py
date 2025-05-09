"""
Kontroler do operacji na użytkownikach
"""
import sys
import os
import re # Added for email validation
from flask import current_app
from pathlib import Path
from sqlalchemy.exc import IntegrityError # Import IntegrityError

# Konfiguracja ścieżek
module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if module_path not in sys.path:
    sys.path.append(module_path)

from __init__ import db
from models.user import User

class UserController:
    @staticmethod
    def get_all_users():
        """Pobiera wszystkich użytkowników"""
        try:
            users = User.query.all()
            return [user.to_dict() for user in users], None
        except Exception as e:
            current_app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while retrieving users"
    
    @staticmethod
    def register_user(data):
        """Rejestruje nowego użytkownika"""
        try:
            # Sprawdź wymagane pola
            required_fields = ['fullName', 'email', 'password']
            for field in required_fields:
                if field not in data or not data[field].strip():
                    return None, f"Field {field} is required", 400
            
            fullName = data['fullName'].strip()
            email = data['email'].strip()
            password = data['password'] # Keep as is for now, strip whitespace if needed during set_password

            # Walidacja fullName
            if not (1 <= len(fullName) <= 80):
                return None, "Full name must be between 1 and 80 characters.", 400

            # Walidacja email
            email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$".strip()
            if not re.match(email_regex, email):
                return None, "Invalid email format.", 400

            # Walidacja hasła
            if len(password) < 6:
                return None, "Password must be at least 6 characters long.", 400

            # Sprawdź, czy użytkownik o podanym adresie email już istnieje
            if User.query.filter_by(email=email).first():
                return None, "User with this email already exists", 409
            
            # Sprawdź, czy użytkownik o podanej nazwie użytkownika (fullName) już istnieje
            # Jeśli username ma być unikalne, to odkomentuj poniższy blok
            # if User.query.filter_by(username=fullName).first():
            #     return None, "User with this username already exists", 409

            # Tworzenie nowego użytkownika
            new_user = User(
                username=fullName,
                email=email,
                is_admin=False
            )
            
            # Bezpieczne ustawienie hasła
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            # Zwróć dane nowego użytkownika bez hasła
            return new_user, None, 201 # Return user object, no error, status 201
        except IntegrityError as e: # Przechwytywanie konkretnego błędu bazy danych
            db.session.rollback()
            current_app.logger.error(f"Registration IntegrityError: {str(e)}")
            # Sprawdzenie, czy błąd dotyczy email, czy username (jeśli username miałoby być unikalne)
            if 'users.email' in str(e).lower():
                 return None, "User with this email already exists.", 409
            # Można dodać podobne sprawdzenie dla 'users.username', jeśli byłoby unikalne
            # elif 'users.username' in str(e).lower():
            #     return None, "This username is already taken.", 409
            return None, "Registration failed due to a database conflict.", 409
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Generic registration error: {str(e)}")
            return None, "An unexpected error occurred during registration.", 500
    
    @staticmethod
    def login_user(email, password):
        """Logowanie użytkownika"""
        try:
            # Sprawdź wymagane pola
            if not email or not password:
                return None, "Email and password are required"
            
            # Znajdź użytkownika po emailu
            user = User.query.filter_by(email=email).first()
            
            # Sprawdź czy użytkownik istnieje i czy hasło jest poprawne
            if not user or not user.check_password(password):
                return None, "Invalid email or password"
              # Zwróć dane użytkownika
            return user.to_dict(), None
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            return None, f"Login failed: {str(e)}"
    
    @staticmethod
    def update_user_avatar(user_id, avatar_url):
        """Aktualizuje awatar użytkownika"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            user.avatar_url = avatar_url
            db.session.commit()
            
            return user.to_dict(), None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Avatar update error: {str(e)}")
            return None, f"Avatar update failed: {str(e)}"

    @staticmethod
    def update_user_data(user_id, data):
        """Aktualizuje dane użytkownika (fullName, email)"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found", 404

            # app.py already ensures data is not empty and contains only relevant keys.
            # Validate and update fullName (username)
            if 'fullName' in data:
                fullName = data['fullName'].strip()
                if not fullName: # Check if stripping results in empty string
                    return None, "Full name cannot be empty if provided for update.", 400
                if not (1 <= len(fullName) <= 80):
                    return None, "Full name must be between 1 and 80 characters.", 400
                user.username = fullName
            
            # Validate and update email
            if 'email' in data:
                email = data['email'].strip()
                if not email: # Check if stripping results in empty string
                    return None, "Email cannot be empty if provided for update.", 400
                
                email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$".strip() # Regex itself doesn't need strip, but kept for consistency if copied
                if not re.match(email_regex, email):
                    return None, "Invalid email format.", 400
                
                # Check for email uniqueness only if the email is actually changing
                if email != user.email:
                    existing_user_with_email = User.query.filter(User.email == email, User.id != user_id).first()
                    if existing_user_with_email:
                        return None, "Email already in use by another account.", 409
                user.email = email
            
            db.session.commit() # SQLAlchemy is smart enough to not issue an UPDATE if values haven't changed
            return user, None, 200 # Return updated user object
        except IntegrityError as e: 
            db.session.rollback()
            current_app.logger.error(f"User data update IntegrityError: {str(e)}")
            if 'users.email' in str(e).lower(): # Defensive check
                 return None, "Email already in use by another account.", 409
            return None, "Update failed due to a database conflict.", 409
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"User data update error: {str(e)}")
            return None, f"User data update failed: {str(e)}", 500

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Zmienia hasło użytkownika"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found", 404

            if not current_password or not new_password: # Basic check for empty inputs
                return None, "Current password and new password are required.", 400

            if not user.check_password(current_password):
                return None, "Invalid current password", 403 # 403 Forbidden might be more appropriate

            # Validate new_password (strip to ensure it's not just whitespace)
            new_password_stripped = new_password.strip()
            if not new_password_stripped:
                return None, "New password cannot be empty or just whitespace.", 400
            
            if len(new_password_stripped) < 6: # Zgodnie z walidacją frontendu
                return None, "Password must be at least 6 characters long", 400

            user.set_password(new_password_stripped)
            db.session.commit()
            return {"message": "Password changed successfully"}, None, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password change error: {str(e)}")
            return None, f"Password change failed: {str(e)}", 500
            
    @staticmethod
    def update_users(users_data):
        """Aktualizuje dane wielu użytkowników"""
        try:
            updated_count = 0
            new_count = 0
            
            for user_data in users_data:
                # Sprawdź czy użytkownik o danym id już istnieje
                user_id = user_data.get('id')
                if user_id:
                    existing_user = User.query.get(user_id)
                    if existing_user:
                        # Aktualizuj istniejącego użytkownika
                        existing_user.username = user_data.get('fullName', existing_user.username)
                        existing_user.email = user_data.get('email', existing_user.email)
                        if 'password' in user_data:
                            existing_user.set_password(user_data['password'])
                        existing_user.is_admin = user_data.get('isAdmin', existing_user.is_admin)
                        updated_count += 1
                        continue
                
                # Jeśli nie znaleziono użytkownika o danym id, sprawdź czy istnieje użytkownik o tym samym emailu
                email = user_data.get('email')
                if email:
                    existing_user = User.query.filter_by(email=email).first()
                    if existing_user:
                        # Aktualizuj istniejącego użytkownika
                        existing_user.username = user_data.get('fullName', existing_user.username)
                        if 'password' in user_data:
                            existing_user.set_password(user_data['password'])
                        existing_user.is_admin = user_data.get('isAdmin', existing_user.is_admin)
                        updated_count += 1
                        continue
                
                # Jeśli nie znaleziono użytkownika, stwórz nowego
                if 'fullName' in user_data and 'email' in user_data:
                    new_user = User(
                        username=user_data['fullName'],
                        email=user_data['email'],
                        is_admin=user_data.get('isAdmin', False)
                    )
                    
                    # Bezpieczne ustawienie hasła
                    if 'password' in user_data:
                        new_user.set_password(user_data['password'])
                    
                    db.session.add(new_user)
                    new_count += 1
            
            if updated_count > 0 or new_count > 0:
                db.session.commit()
            
            return {
                'success': True,
                'updatedCount': updated_count,
                'newCount': new_count
            }, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating users: {str(e)}")
            return None, f"Failed to update users: {str(e)}"
