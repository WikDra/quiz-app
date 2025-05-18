import os
import sys
import importlib.util

def test_oauth_setup():
    """Test OAuth controller initialization"""
    # Add the backend directory to the Python path
    backend_dir = os.path.abspath(os.path.dirname(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    # Load the module
    spec = importlib.util.spec_from_file_location(
        "oauth_controller", 
        os.path.join(backend_dir, "controllers", "oauth_controller.py")
    )
    oauth_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oauth_module)
    
    # Create a mock Flask app
    from flask import Flask
    app = Flask(__name__)
    
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize OAuth
    oauth = oauth_module.init_oauth(app)
    
    # Check if it was initialized properly
    if hasattr(oauth, 'google'):
        print("OAuth initialized successfully!")
        print(f"Google client ID: {'*' * len(oauth.google.client_id) if oauth.google.client_id else 'Not set'}")
        print(f"Registration status: {'Registered' if oauth.google.client_id else 'Not registered'}")
    else:
        print("OAuth initialization failed!")

if __name__ == "__main__":
    test_oauth_setup()
