"""
Direct script to create and test cookies and JWT authentication
"""
import os
import sys
import json
import requests
from pprint import pprint

# Add parent directory to import modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

BASE_URL = "http://localhost:5000"

def test_cookies():
    """Test cookie setting and retrieval"""
    print("\n=== TESTING COOKIES ===")
    
    # First test the basic cookie setting endpoint
    response = requests.get(f"{BASE_URL}/api/test-cookies")
    print(f"Status: {response.status_code}")
    print(f"Cookies set: {response.cookies.keys()}")
    
    # Now try to use these cookies in another request
    cookies = response.cookies
    if cookies:
        print("\nTesting cookie reuse...")
        response2 = requests.get(f"{BASE_URL}/api/debug/auth", cookies=cookies)
        print(f"Status: {response2.status_code}")
        if response2.status_code == 200:
            pprint(response2.json())
    
    print("\n=== TEST COMPLETED ===")

def test_login():
    """Test direct login with credentials"""
    print("\n=== TESTING LOGIN ===")
    
    # Use existing credentials (replace with real credentials)
    login_data = {
        "email": "test@example.com",
        "password": "testpassword" 
    }
    
    response = requests.post(
        f"{BASE_URL}/api/login", 
        json=login_data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Cookies set: {response.cookies.keys()}")
    
    # If login succeeded, test the profile access
    if response.status_code == 200 and response.cookies:
        print("\nTesting profile access...")
        profile_response = requests.get(
            f"{BASE_URL}/api/users/me/profile",
            cookies=response.cookies  
        )
        
        print(f"Profile status: {profile_response.status_code}")
        if profile_response.status_code == 200:
            pprint(profile_response.json())
        else:
            print("Profile access failed")
            if profile_response.text:
                try:
                    pprint(profile_response.json())
                except:
                    print(profile_response.text)
    
    print("\n=== TEST COMPLETED ===")

def create_test_user():
    """Create a test user for login"""
    print("\n=== CREATING TEST USER ===")
    
    # Test user data
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    # Try to register
    response = requests.post(f"{BASE_URL}/api/register", json=user_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        print("User created successfully!")
        pprint(response.json())
    else:
        print("Failed to create user")
        if response.text:
            try:
                pprint(response.json())
            except:
                print(response.text)
    
    print("\n=== TEST COMPLETED ===")

def test_profile_directly():
    """Test direct access to profile endpoint with session/cookies"""
    print("\n=== TESTING DIRECT PROFILE ACCESS ===")
    
    # Create a persistent session to maintain cookies
    session = requests.Session()
    
    # First login
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123" 
    }
    
    login_response = session.post(f"{BASE_URL}/api/login", json=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # Now try to access profile using the same session (cookies will be sent automatically)
        profile_response = session.get(f"{BASE_URL}/api/users/me/profile")
        print(f"Profile status: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            pprint(profile_response.json())
        else:
            print("Profile access failed")
            if profile_response.text:
                try:
                    pprint(profile_response.json())
                except:
                    print(profile_response.text)
                    
        # Print session cookies
        print("\nSession cookies:")
        for cookie in session.cookies:
            print(f"  {cookie.name}: {cookie.value} (Domain: {cookie.domain}, Path: {cookie.path}, SameSite: {cookie.get('samesite', 'Not Set')})")
    else:
        print("Login failed, cannot test profile")
        if login_response.text:
            try:
                pprint(login_response.json())
            except:
                print(login_response.text)
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    # Test basic cookie functionality
    test_cookies()
    
    # Create a test user if needed
    # create_test_user()
    
    # Test login
    # test_login()
    
    # Test profile access
    # test_profile_directly()
