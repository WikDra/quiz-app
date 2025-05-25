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
    user = User.query.filter_by(email="test@test.pl").first()
    if user:
        print(f"Użytkownik: {user.email}")
        print(f"Password hash: {user.password_hash}")
        
        # Test różnych haseł
        passwords_to_test = [
            "Hasło123!",
            "Haslo123!",
            "hasło123!",
            "HASŁO123!",
            "Hasło123",
            "hasło123"
        ]
        
        for pwd in passwords_to_test:
            result = check_password_hash(user.password_hash, pwd)
            print(f"Hasło '{pwd}': {result}")
            
        # Test bezpośrednio przez metodę modelu
        print("\nTest przez metodę modelu:")
        for pwd in passwords_to_test:
            result = user.check_password(pwd)
            print(f"Hasło '{pwd}': {result}")
    else:
        print("Nie znaleziono użytkownika test@test.pl")
