"""
Scheduled tasks for the application
"""
import threading
import time
from flask import current_app
from app.user_controller import TokenBlacklistManager


def cleanup_expired_tokens():
    """
    Clean up expired blacklisted tokens from the database
    This function is designed to be run periodically
    """
    try:
        expired_count = TokenBlacklistManager.cleanup_expired_tokens()
        current_app.logger.info(f"Scheduled cleanup: Removed {expired_count} expired blacklisted tokens")
        return expired_count
    except Exception as e:
        current_app.logger.error(f"Error in scheduled token cleanup: {str(e)}")
        return 0


def setup_scheduled_tasks(app):
    """
    Setup scheduled tasks for the application
    
    Args:
        app: Flask application instance
    """
    
    def run_cleanup_loop():
        """Run cleanup task periodically in a separate thread"""
        while True:
            try:
                time.sleep(3600)  # Wait 1 hour (3600 seconds)
                with app.app_context():
                    cleanup_expired_tokens()
            except Exception as e:
                app.logger.error(f"Error in cleanup loop: {str(e)}")
                time.sleep(3600)  # Wait before retrying
    
    # Start cleanup in a daemon thread
    cleanup_thread = threading.Thread(target=run_cleanup_loop, daemon=True)
    cleanup_thread.start()
    
    app.logger.info("Token cleanup scheduler initialized (runs every hour)")


def manual_cleanup_expired_tokens(app):
    """
    Manually trigger cleanup of expired tokens
    Useful for testing or manual maintenance
    
    Args:
        app: Flask application instance
        
    Returns:
        int: Number of tokens cleaned up
    """
    with app.app_context():
        return cleanup_expired_tokens()
