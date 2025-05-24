#!/usr/bin/env python3
"""
Database Migration Script for Admin Panel Features
Adds role field to User model and creates OfflinePayment table
"""

import sys
import os

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, OfflinePayment
from sqlalchemy import text

def run_migration():
    """Run the database migration"""
    app = create_app()
    
    with app.app_context():
        print("Starting database migration...")
        
        try:
            # Check if role column exists in User table
            result = db.engine.execute(text("PRAGMA table_info(user)"))
            columns = [row[1] for row in result]
            
            if 'role' not in columns:
                print("Adding 'role' column to User table...")
                db.engine.execute(text("ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
                print("✓ Role column added successfully")
            else:
                print("✓ Role column already exists")
            
            # Check if OfflinePayment table exists
            result = db.engine.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='offline_payment'"))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                print("Creating OfflinePayment table...")
                # Create all tables (this will create OfflinePayment if it doesn't exist)
                db.create_all()
                print("✓ OfflinePayment table created successfully")
            else:
                print("✓ OfflinePayment table already exists")
            
            # Update existing users to have 'user' role if they don't have one
            print("Updating existing users with default role...")
            db.engine.execute(text("UPDATE user SET role = 'user' WHERE role IS NULL OR role = ''"))
            print("✓ Existing users updated with default role")
            
            db.session.commit()
            print("\n✅ Migration completed successfully!")
            print("📋 Summary:")
            print("   - User table now has 'role' field")
            print("   - OfflinePayment table created")
            print("   - Existing users assigned 'user' role")
            print("   - Admin functionality is now available")
            print("\n💡 Next steps:")
            print("   1. Create an admin user with: python create_admin.py")
            print("   2. Restart the Flask application")
            print("   3. Login as admin to access /admin panel")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    run_migration()
