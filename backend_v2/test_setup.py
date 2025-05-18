"""
Test script to verify backend configuration
"""
import os
import sys
import requests
from dotenv import load_dotenv

def test_backend():
    """Test basic backend functionality"""
    print("Testing backend configuration...")
    
    # Test environment variables
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print(f"✅ .env file found at {dotenv_path}")
    else:
        print(f"❌ .env file not found at {dotenv_path}")
        print("   Please run utils/setup_security.py first.")
        return False
    
    # Test Google OAuth credentials
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    if google_client_id and google_client_secret:
        print("✅ Google OAuth credentials found in .env")
    else:
        print("❌ Google OAuth credentials missing from .env")
        print("   Please run utils/setup_security.py to configure OAuth.")
        return False
    
    # Test if backend is running
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=2)
        if response.status_code == 200:
            print("✅ Backend server is running")
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"❌ Backend server returned status code {response.status_code}")
            print("   Make sure the server is running with `python run.py`")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("   Make sure the server is running with `python run.py`")
        return False
    except Exception as e:
        print(f"❌ Error testing backend server: {str(e)}")
        return False
    
    print("\nTest completed successfully!")
    print("Your backend appears to be properly configured.")
    return True

if __name__ == "__main__":
    test_backend()
