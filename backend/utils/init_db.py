"""
Database initialization script to ensure all tables exist
"""
import os
import sys
import logging

# Add parent directory to path so we can import modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Flask app and models
from models import db
from models.user import User
from models.quiz import Quiz

def init_database():
    """Initialize the database and create all tables"""
    from app import app
    
    with app.app_context():
        logger.info("Creating all database tables...")
        db.create_all()
          # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(f"Database tables: {', '.join(tables)}")
        
        # Check if important tables exist
        if 'users' not in tables:
            logger.error("'users' table was not created!")
        else:
            logger.info("'users' table exists.")
            # Verify 'has_premium_access' column in 'users' table
            columns = [col['name'] for col in inspector.get_columns('users')]
            if 'has_premium_access' in columns:
                logger.info("'has_premium_access' column exists in 'users' table.")
            else:
                logger.error("'has_premium_access' column DOES NOT exist in 'users' table!")
            
        if 'quizzes' not in tables:
            logger.error("'quizzes' table was not created!")
        else:
            logger.info("'quizzes' table exists.")
            
        return tables

if __name__ == "__main__":
    tables = init_database()
    print(f"Database initialized with tables: {', '.join(tables)}")
