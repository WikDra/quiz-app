"""
Script to initialize and check the database
"""
import os
import sys
from flask import Flask
from dotenv import load_dotenv

# Set up path to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db
from models.user import User
from models.quiz import Quiz

def create_app():
    """Create a minimal Flask app for database initialization"""
    app = Flask(__name__)
    
    # Load environment variables
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print(f"Loaded environment variables from {dotenv_path}")
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'quiz_app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    return app

def check_database():
    """Check and initialize the database"""
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("Database tables created (if they didn't exist already)")
        
        # Check if tables exist
        try:
            user_count = User.query.count()
            print(f"Users table exists with {user_count} records")
        except Exception as e:
            print(f"Error checking Users table: {str(e)}")
        
        try:
            quiz_count = Quiz.query.count()
            print(f"Quizzes table exists with {quiz_count} records")
        except Exception as e:
            print(f"Error checking Quizzes table: {str(e)}")
        
        # List all tables in database
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("\nTables in the database:", tables)
        
        # For each table, show columns
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            print(f"\nColumns in {table_name}:")
            for column in columns:
                print(f"  - {column['name']} ({column['type']})")

if __name__ == "__main__":
    check_database()
