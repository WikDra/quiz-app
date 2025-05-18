"""
Debug script to inspect JWT cookie handling
"""
import os
import sys
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

def debug_jwt():
    """Debug JWT cookie configuration and handling"""
    # Import app for access to JWT manager and configurations
    from app import app
    from flask_jwt_extended import create_access_token, decode_token
    from flask import make_response, jsonify, request
    
    print("\n===== JWT DEBUG INFO =====")
    print(f"JWT_TOKEN_LOCATION: {app.config.get('JWT_TOKEN_LOCATION')}")
    print(f"JWT_COOKIE_SECURE: {app.config.get('JWT_COOKIE_SECURE')}")
    print(f"JWT_COOKIE_CSRF_PROTECT: {app.config.get('JWT_COOKIE_CSRF_PROTECT')}")
    print(f"JWT_COOKIE_SAMESITE: {app.config.get('JWT_COOKIE_SAMESITE')}")
    print(f"JWT_ACCESS_TOKEN_EXPIRES: {app.config.get('JWT_ACCESS_TOKEN_EXPIRES')}")
    
    # Create a test token
    with app.app_context():
        test_token = create_access_token(identity=999)
        print(f"\nTest token: {test_token[:20]}...")
        
        # Decode the token to check its contents
        try:
            decoded = decode_token(test_token)
            print("\nDecoded token:")
            print(json.dumps(decoded, indent=2, default=str))
        except Exception as e:
            print(f"Error decoding token: {e}")
        
        # Check app.after_request handler to ensure cookie attributes are set correctly
        original_after_request = None
        for handler in app.after_request_funcs.get(None, []):
            if handler.__name__ == 'set_cookie_attributes':
                original_after_request = handler
                print(f"\nFound set_cookie_attributes after_request handler: {handler}")
                break
        
        if original_after_request:
            # Create a test response with a cookie
            test_response = make_response(jsonify({"message": "Test response"}))
            test_response.set_cookie('test_cookie', 'test_value', samesite='Lax')
            
            # Run the after_request handler
            modified_response = original_after_request(test_response)
            
            # Check cookie headers
            print("\nCookie headers after modification:")
            for header in modified_response.headers.getlist('Set-Cookie'):
                print(f" - {header}")
        else:
            print("No set_cookie_attributes after_request handler found")
    
    print("\n===== END JWT DEBUG INFO =====")

if __name__ == "__main__":
    debug_jwt()
