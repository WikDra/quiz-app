#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User
from app.extensions import db

app = create_app()

with app.app_context():
    user = User.query.filter_by(email="test@test.pl").first()
    if user:
        print(f"Updating password for user: {user.email}")
        user.set_password("Haslo123!")
        db.session.commit()
        print("Password updated successfully!")
        
        # Test nowego hasła
        result = user.check_password("Haslo123!")
        print(f"New password test: {result}")
    else:
        print("User not found!")
