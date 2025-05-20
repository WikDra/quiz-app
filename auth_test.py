# auth_test.py
"""
Test script for JWT authentication in Flask backend
This script helps diagnose JWT token issues and cookies
"""
import os
import sys
import json
import requests
import argparse
from pprint import pprint

def test_auth(api_url, email, password):
    """Test JWT authentication flow"""
    session = requests.Session()
    
    print("\n==== JWT Authentication Test ====\n")
    
    # Step 1: Test API health
    print("1. Testing API health...")
    try:
        response = session.get(f"{api_url}/api/health")
        response.raise_for_status()
        print(f"✅ API is healthy: {response.json()}")
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return
    
    # Step 2: Attempt login
    print("\n2. Attempting login...")
    try:
        response = session.post(
            f"{api_url}/api/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            print("✅ Login successful")
            print("\nUser data:")
            pprint(response.json())
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return
    
    # Step 3: Check cookies
    print("\n3. Checking cookies...")
    cookies = session.cookies
    jwt_access = cookies.get("access_token_cookie")
    jwt_refresh = cookies.get("refresh_token_cookie")
    
    if jwt_access:
        print("✅ Found access_token_cookie")
    else:
        print("❌ No access_token_cookie found")
    
    if jwt_refresh:
        print("✅ Found refresh_token_cookie")
    else:
        print("❌ No refresh_token_cookie found")
    
    print("\nAll cookies:")
    for cookie in cookies:
        print(f"  - {cookie.name}: {'[set]' if cookie.value else '[empty]'}")
    
    # Step 4: Verify token with user profile
    print("\n4. Verifying token with user profile endpoint...")
    try:
        response = session.get(f"{api_url}/api/users/me/profile")
        
        if response.status_code == 200:
            print("✅ Token verification successful")
            print("\nProfile data:")
            pprint(response.json())
        else:
            print(f"❌ Token verification failed with status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Token verification request failed: {e}")
    
    # Step 5: Test token refresh
    print("\n5. Testing token refresh...")
    try:
        response = session.post(f"{api_url}/api/token/refresh")
        
        if response.status_code == 200:
            print("✅ Token refresh successful")
            
            # Check if new access token cookie was set
            new_cookies = session.cookies
            new_access = new_cookies.get("access_token_cookie")
            
            if new_access and new_access != jwt_access:
                print("✅ New access token set in cookies")
            else:
                print("❌ No new access token in cookies")
        else:
            print(f"❌ Token refresh failed with status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Token refresh request failed: {e}")
    
    # Step 6: Test logout
    print("\n6. Testing logout...")
    try:
        response = session.post(f"{api_url}/api/logout")
        
        if response.status_code == 200:
            print("✅ Logout successful")
            
            # Check if cookies were cleared
            cookies_after_logout = session.cookies
            jwt_access_after = cookies_after_logout.get("access_token_cookie")
            jwt_refresh_after = cookies_after_logout.get("refresh_token_cookie")
            
            if not jwt_access_after:
                print("✅ Access token cookie cleared")
            else:
                print("❌ Access token cookie not cleared")
            
            if not jwt_refresh_after:
                print("✅ Refresh token cookie cleared")
            else:
                print("❌ Refresh token cookie not cleared")
        else:
            print(f"❌ Logout failed with status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Logout request failed: {e}")
    
    print("\n==== Auth Test Complete ====\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test JWT authentication")
    parser.add_argument("--url", default="http://localhost:5000", help="API base URL")
    parser.add_argument("--email", default="test@example.com", help="Login email")
    parser.add_argument("--password", default="password123", help="Login password")
    
    args = parser.parse_args()
    
    test_auth(args.url, args.email, args.password)
