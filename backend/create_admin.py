"""
Script to create the first admin user
Run this script to create an admin account
"""
import sys
import os

# Add the parent directory to Python path to import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.models import User
from app.extensions import db

def create_admin_user():
    """Create the first admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(role='admin').first()
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.email}")
            return
        
        # Create admin user
        admin_email = input("Enter admin email: ").strip()
        admin_username = input("Enter admin username: ").strip()
        admin_password = input("Enter admin password: ").strip()
        
        if not admin_email or not admin_username or not admin_password:
            print("All fields are required!")
            return
        
        # Check if user with this email already exists
        existing_user = User.query.filter_by(email=admin_email).first()
        if existing_user:
            # Promote existing user to admin
            existing_user.promote_to_admin()
            db.session.commit()
            print(f"User {existing_user.email} promoted to admin!")
        else:
            # Create new admin user
            admin_user = User(
                username=admin_username,
                email=admin_email,
                role='admin'
            )
            admin_user.set_password(admin_password)
            admin_user.promote_to_admin()
            
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user created: {admin_email}")

if __name__ == "__main__":
    create_admin_user()
