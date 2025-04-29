"""
Data migration script to transfer quiz and user data from JSON files to SQLite database.
Run this after database initialization to populate the database with existing data.
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path to allow imports from app
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Import aplikacji Flask i modeli
from app import create_app, db
from app.models.user import User
from app.models.quiz import Quiz

# JSON file paths - aktualizacja ścieżek względem projektu
PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUIZ_JSON_PATH = PROJECT_ROOT / 'public' / 'quiz.json'
USERS_JSON_PATH = PROJECT_ROOT / 'public' / 'users.json'

def load_json_data(file_path):
    """Load data from a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return None

def migrate_users(users_data):
    """Migrate user data from JSON to database"""
    if not users_data:
        print("No users data to migrate.")
        return 0
    
    count = 0
    for user_data in users_data:
        # Check if user already exists
        existing_user = User.query.filter_by(username=user_data.get('username')).first()
        if existing_user:
            print(f"User {user_data.get('username')} already exists. Skipping.")
            continue
            
        # Create new user
        new_user = User(
            username=user_data.get('username'),
            email=user_data.get('email', f"{user_data.get('username')}@example.com"),
            # No password hash for now, users will need to reset password
            is_admin=user_data.get('isAdmin', False)
        )
        db.session.add(new_user)
        count += 1
    
    if count > 0:
        db.session.commit()
        print(f"Successfully migrated {count} users.")
    else:
        print("No new users were migrated.")
    
    return count

def migrate_quizzes(quizzes_data):
    """Migrate quiz data from JSON to database"""
    if not quizzes_data or 'quizzes' not in quizzes_data:
        print("No quiz data to migrate or invalid format.")
        return 0
    
    count = 0
    for quiz_data in quizzes_data['quizzes']:
        # Check if quiz already exists (by title as unique identifier)
        existing_quiz = Quiz.query.filter_by(title=quiz_data.get('title')).first()
        if existing_quiz:
            print(f"Quiz '{quiz_data.get('title')}' already exists. Skipping.")
            continue
        
        # Find user_id if available
        user_id = None
        if 'author' in quiz_data:
            user = User.query.filter_by(username=quiz_data['author']).first()
            if user:
                user_id = user.id
        
        # Create new quiz
        new_quiz = Quiz(
            title=quiz_data.get('title'),
            description=quiz_data.get('description'),
            category=quiz_data.get('category'),
            difficulty=quiz_data.get('difficulty'),
            user_id=user_id
        )
        
        # Set questions using the property setter
        new_quiz.questions = quiz_data.get('questions', [])
        
        db.session.add(new_quiz)
        count += 1
    
    if count > 0:
        db.session.commit()
        print(f"Successfully migrated {count} quizzes.")
    else:
        print("No new quizzes were migrated.")
    
    return count

def main():
    """Main function to run the data migration"""
    print("Starting data migration from JSON to MySQL...")
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        # Load JSON data
        users_data = load_json_data(USERS_JSON_PATH)
        quizzes_data = load_json_data(QUIZ_JSON_PATH)
        
        # Migrate users first (needed for foreign key relationships)
        if users_data:
            migrate_users(users_data)
        
        # Migrate quizzes
        if quizzes_data:
            migrate_quizzes(quizzes_data)
            
    print("Data migration completed!")

if __name__ == "__main__":
    main()
