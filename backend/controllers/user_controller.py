"""
Kontroler do operacji na użytkownikach
"""
import sys
import os
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
                    return None, f"Field {field} is required"
            
            # Sprawdź, czy użytkownik o podanym adresie email już istnieje
            if User.query.filter_by(email=data['email']).first():
                return None, "User with this email already exists"
            
            # Sprawdź, czy użytkownik o podanej nazwie użytkownika (fullName) już istnieje
            # Jeśli username ma być unikalne, to odkomentuj poniższy blok
            # if User.query.filter_by(username=data['fullName']).first():
            #     return None, "User with this username already exists"

            # Tworzenie nowego użytkownika
            new_user = User(
                username=data['fullName'],
                email=data['email'],
                is_admin=False
            )
            
            # Bezpieczne ustawienie hasła
            new_user.set_password(data['password'])
            
            db.session.add(new_user)
            db.session.commit()
            
            # Zwróć dane nowego użytkownika bez hasła
            return new_user.to_dict(), None
        except IntegrityError as e: # Przechwytywanie konkretnego błędu bazy danych
            db.session.rollback()
            current_app.logger.error(f"Registration IntegrityError: {str(e)}")
            # Sprawdzenie, czy błąd dotyczy email, czy username (jeśli username miałoby być unikalne)
            if 'users.email' in str(e).lower():
                 return None, "User with this email already exists."
            # Można dodać podobne sprawdzenie dla 'users.username', jeśli byłoby unikalne
            # elif 'users.username' in str(e).lower():
            #     return None, "This username is already taken."
            return None, "Registration failed due to a database conflict. Please try different data."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Generic registration error: {str(e)}")
            return None, "An unexpected error occurred during registration. Please try again."
    
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
                return None, "User not found"

            # Walidacja i aktualizacja fullName (username)
            if 'fullName' in data and data['fullName'].strip():
                user.username = data['fullName'].strip()
            
            # Walidacja i aktualizacja email
            if 'email' in data and data['email'].strip():
                # Sprawdź, czy nowy email nie jest już zajęty przez innego użytkownika
                existing_user_with_email = User.query.filter(User.email == data['email'].strip(), User.id != user_id).first()
                if existing_user_with_email:
                    return None, "Email already in use by another account"
                user.email = data['email'].strip()
            
            db.session.commit()
            return user.to_dict(), None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"User data update error: {str(e)}")
            return None, f"User data update failed: {str(e)}"

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Zmienia hasło użytkownika"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"

            if not user.check_password(current_password):
                return None, "Invalid current password"

            if len(new_password) < 6: # Zgodnie z walidacją frontendu
                return None, "Password must be at least 6 characters long"

            user.set_password(new_password)
            db.session.commit()
            return {"message": "Password changed successfully"}, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password change error: {str(e)}")
            return None, f"Password change failed: {str(e)}"
            
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
