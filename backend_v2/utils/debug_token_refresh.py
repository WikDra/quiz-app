#!/usr/bin/env python3
"""
Debug script to check and fix JWT token refresh functionality
"""
import os
import sys
import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add parent directory to sys.path to import from backend_v2
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend_v2.app import create_app
from backend_v2.models import db

def main():
    """Main function to debug and fix token refresh"""
    app = create_app()
    
    with app.app_context():
        # Check JWT configuration
        print("\n=== JWT Configuration ===")
        print(f"JWT_TOKEN_LOCATION: {app.config.get('JWT_TOKEN_LOCATION')}")
        print(f"JWT_ACCESS_TOKEN_EXPIRES: {app.config.get('JWT_ACCESS_TOKEN_EXPIRES')}")
        print(f"JWT_REFRESH_TOKEN_EXPIRES: {app.config.get('JWT_REFRESH_TOKEN_EXPIRES')}")
        print(f"JWT_COOKIE_SECURE: {app.config.get('JWT_COOKIE_SECURE')}")
        print(f"JWT_COOKIE_CSRF_PROTECT: {app.config.get('JWT_COOKIE_CSRF_PROTECT')}")
        print(f"JWT_COOKIE_SAMESITE: {app.config.get('JWT_COOKIE_SAMESITE')}")
        
        # Check CORS configuration
        print("\n=== CORS Configuration ===")
        cors_configs = [app.extensions.get('cors', None)]
        
        if cors_configs[0] is not None:
            print(f"Origins: {cors_configs[0]._origins}")
            print(f"Supports Credentials: {cors_configs[0]._supports_credentials}")
            print(f"Allow Headers: {cors_configs[0]._allow_headers}")
            print(f"Expose Headers: {cors_configs[0]._expose_headers}")
            print(f"Methods: {cors_configs[0]._methods}")
        else:
            print("CORS not properly configured")
    
    # Create test route for token refresh with proper error handling
    @app.route('/api/test-token-refresh', methods=['POST'])
    def test_token_refresh():
        """Test endpoint to debug token refresh issues"""
        try:
            # Log request details
            app.logger.info("Received test token refresh request")
            app.logger.info(f"Request headers: {request.headers}")
            app.logger.info(f"Request cookies: {request.cookies}")
            
            # Simple response with CORS headers
            response = jsonify({"message": "Token refresh test successful"})
            return response
        except Exception as e:
            app.logger.error(f"Error in test token refresh: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    # Run the app in debug mode
    app.run(debug=True, host='127.0.0.1', port=5001)

if __name__ == "__main__":
    main()
