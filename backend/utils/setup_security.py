"""
Utility script to generate security keys and OAuth credentials
"""
import os
import base64
import secrets
import json
from dotenv import load_dotenv, set_key

def generate_key(length=32):
    """Generate a secure random key"""
    return base64.b64encode(secrets.token_bytes(length)).decode('utf-8')

def setup_security():
    """Set up security keys and OAuth credentials"""
    # Get the path to the .env file
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    # Create or load .env file
    if os.path.exists(dotenv_path):
        print(f"Loading existing .env file: {dotenv_path}")
        load_dotenv(dotenv_path)
    else:
        print(f"Creating new .env file: {dotenv_path}")
        with open(dotenv_path, 'w', encoding='utf-8') as f:
            f.write("# Plik konfiguracyjny dla Quiz App - wygenerowany automatycznie\n")
            f.write("# UWAGA: Ten plik zawiera poufne dane - nie umieszczaj go w repozytorium kodu!\n\n")
    
    # Generate SECRET_KEY if doesn't exist
    if not os.environ.get('SECRET_KEY'):
        secret_key = generate_key()
        set_key(dotenv_path, 'SECRET_KEY', secret_key)
        print("Generated new SECRET_KEY")
    else:
        print("Using existing SECRET_KEY")
    
    # Generate JWT_SECRET_KEY if doesn't exist
    if not os.environ.get('JWT_SECRET_KEY'):
        jwt_secret_key = generate_key()
        set_key(dotenv_path, 'JWT_SECRET_KEY', jwt_secret_key)
        print("Generated new JWT_SECRET_KEY")
    else:
        print("Using existing JWT_SECRET_KEY")
    
    # Set FRONTEND_URL if doesn't exist
    if not os.environ.get('FRONTEND_URL'):
        set_key(dotenv_path, 'FRONTEND_URL', 'http://127.0.0.1:5173')
        print("Set default FRONTEND_URL to http://127.0.0.1:5173")
    else:
        print(f"Using existing FRONTEND_URL: {os.environ.get('FRONTEND_URL')}")
    
    # Setup Google OAuth credentials
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    if not google_client_id or not google_client_secret:
        print("\nGoogle OAuth credentials not found.")
        print("To set up Google OAuth, you need to:")
        print("1. Go to Google Developer Console: https://console.developers.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Go to 'Credentials' and create an OAuth 2.0 Client ID")
        print("4. Set the authorized redirect URI to: http://127.0.0.1:5000/api/authorize/google")
        print("5. Enter the credentials below:\n")
        
        google_client_id = input("Enter Google Client ID: ")
        google_client_secret = input("Enter Google Client Secret: ")
        
        if google_client_id and google_client_secret:
            set_key(dotenv_path, 'GOOGLE_CLIENT_ID', google_client_id)
            set_key(dotenv_path, 'GOOGLE_CLIENT_SECRET', google_client_secret)
            print("\nGoogle OAuth credentials saved to .env file")
        else:
            print("\nGoogle OAuth credentials not provided. You can set them later in the .env file.")
    else:
        print(f"\nUsing existing Google OAuth credentials")
    
    print("\nSecurity setup complete. The application is now configured with secure keys.")

if __name__ == "__main__":
    setup_security()
