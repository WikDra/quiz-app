#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User
from app.extensions import db
from werkzeug.security import check_password_hash

app = create_app()

with app.app_context():
    users = User.query.all()
    print(f"Znaleziono {len(users)} użytkowników:")
    
    for user in users:
        print(f"\n--- Użytkownik ID {user.id} ---")
        print(f"Email: {user.email}")
        print(f"Username: {user.username}")
        print(f"Google ID: {user.google_id}")
        print(f"Password hash: {user.password_hash[:50] if user.password_hash else 'None'}...")
        
        # Test hasła Hasło123! dla tego użytkownika
        if user.password_hash:
            is_valid = check_password_hash(user.password_hash, "Hasło123!")
            print(f"Hasło 'Hasło123!' pasuje: {is_valid}")
        else:
            print("Brak hasła (OAuth user)")
