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
            logger.info("'users' table exists.")            # Verify premium-related columns in 'users' table
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Check has_premium_access
            if 'has_premium_access' in columns:
                logger.info("'has_premium_access' column exists in 'users' table.")
            else:
                logger.error("'has_premium_access' column DOES NOT exist in 'users' table!")
                
            # Check premium_since
            if 'premium_since' in columns:
                logger.info("'premium_since' column exists in 'users' table.")
            else:
                logger.error("'premium_since' column DOES NOT exist in 'users' table!")
                
        if 'stripe_subscriptions' not in tables:
            logger.error("'stripe_subscriptions' table was not created!")
        else:
            logger.info("'stripe_subscriptions' table exists.")
            columns = [col['name'] for col in inspector.get_columns('stripe_subscriptions')]
            required_columns = [
                'user_id', 'stripe_subscription_id', 'stripe_customer_id', 
                'status', 'current_period_start', 'current_period_end',
                'created_at', 'canceled_at'
            ]
            for col in required_columns:
                if col in columns:
                    logger.info(f"'{col}' column exists in 'stripe_subscriptions' table.")
                else:
                    logger.error(f"'{col}' column DOES NOT exist in 'stripe_subscriptions' table!")
            
        if 'quizzes' not in tables:
            logger.error("'quizzes' table was not created!")
        else:
            logger.info("'quizzes' table exists.")
            
        return tables

if __name__ == "__main__":
    tables = init_database()
    print(f"Database initialized with tables: {', '.join(tables)}")
