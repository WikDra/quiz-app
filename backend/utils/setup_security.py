"""
Security setup utilities
"""
import os
import secrets
import json
from pathlib import Path
from dotenv import load_dotenv, set_key

def generate_secret_key(length=32):
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(length)

def update_env_file():
    """Update .env file with required security settings if they don't exist"""
    env_path = Path(__file__).parent.parent / '.env'
      # Default values for required settings
    required_settings = {
        'FLASK_SECRET_KEY': lambda: generate_secret_key(32),
        'JWT_SECRET_KEY': lambda: generate_secret_key(32),
        'STRIPE_WEBHOOK_SECRET': lambda: 'whsec_test_' + generate_secret_key(24),
        'STRIPE_SECRET_KEY': lambda: 'sk_test_' + generate_secret_key(24),
        'STRIPE_PUBLISHABLE_KEY': lambda: 'pk_test_' + generate_secret_key(24),
    }
    
    # Read existing .env content
    existing_settings = {}
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    existing_settings[key] = value

    # Update settings
    updated = False
    for key, default_value in required_settings.items():
        if key not in existing_settings or not existing_settings[key]:
            existing_settings[key] = default_value()
            updated = True
    
    # Write updated .env file if changes were made
    if updated:
        with open(env_path, 'w', encoding='utf-8') as f:
            for key, value in existing_settings.items():
                f.write(f'{key}={value}\n')
        
        return True
    
    return False

def generate_key(length=32):
    """Generate a secure random key"""
    return secrets.token_urlsafe(length)

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
        set_key(dotenv_path, 'FRONTEND_URL', 'http://localhost:5173')
        print("Set default FRONTEND_URL to http://localhost:5173")
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
    
    # Setup Stripe API keys
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    stripe_secret_key = os.environ.get('STRIPE_SECRET_KEY')
    stripe_webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if not stripe_publishable_key or not stripe_secret_key or not stripe_webhook_secret:
        print("\nStripe API keys not found or incomplete.")
        print("To set up Stripe payment processing, you need to:")
        print("1. Create a Stripe account: https://stripe.com")
        print("2. Get your API keys from the Stripe Dashboard")
        print("3. Set up a webhook endpoint in Stripe for http://your-domain/api/webhook")
        print("4. Enter the credentials below:\n")
        
        stripe_publishable_key = input("Enter Stripe Publishable Key: ")
        stripe_secret_key = input("Enter Stripe Secret Key: ")
        stripe_webhook_secret = input("Enter Stripe Webhook Secret: ")
        
        if stripe_publishable_key and stripe_secret_key and stripe_webhook_secret:
            set_key(dotenv_path, 'STRIPE_PUBLISHABLE_KEY', stripe_publishable_key)
            set_key(dotenv_path, 'STRIPE_SECRET_KEY', stripe_secret_key)
            set_key(dotenv_path, 'STRIPE_WEBHOOK_SECRET', stripe_webhook_secret)
            print("\nStripe API keys saved to .env file")
        else:
            print("\nStripe API keys not provided or incomplete. You can set them later in the .env file.")
    else:
        print(f"\nUsing existing Stripe API keys")
    
    print("\nSecurity setup complete. The application is now configured with secure keys.")

if __name__ == "__main__":
    setup_security()
