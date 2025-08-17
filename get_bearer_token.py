#!/usr/bin/env python3
"""
Script to retrieve bearer tokens for testing the SmartBin API
"""

import requests
import json
import sys
from urllib.parse import urlencode

# Configuration
BACKEND_URL = "http://localhost:8000"
GOOGLE_CLIENT_ID = "your-google-client-id"  # You'll need to set this from your .env file

def get_existing_test_token():
    """Return the existing test token from debug_auth.py"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OGExN2Q1MWJmMmI1NzUwNmMwMWZiMjIiLCJlbWFpbCI6ImFycWlsYXNwQGdtYWlsLmNvbSIsIm5hbWUiOiJBcnFpbGEgU3VyeWEgUHV0cmEiLCJleHAiOjE3NTYwMjQ4MTZ9.MHn47eWmT8lkOpWjIP3SPGvJYi-ItdaGy_mknYemf3U"

def test_token_validity(token):
    """Test if a token is valid by calling the /auth/me endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token is valid!")
            print(f"User: {user_data['name']} ({user_data['email']})")
            print(f"Points: {user_data['points']}")
            return True
        else:
            print(f"❌ Token is invalid. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing token: {e}")
        return False

def get_google_oauth_url():
    """Get the Google OAuth URL for manual authentication"""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": "http://localhost:8000/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline"
    }
    
    oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return oauth_url

def main():
    print("🔑 SmartBin Bearer Token Retrieval Tool")
    print("=" * 50)
    
    # First, try the existing test token
    print("\n1. Testing existing test token...")
    test_token = get_existing_test_token()
    
    if test_token_validity(test_token):
        print(f"\n🎯 Use this bearer token for testing:")
        print(f"Bearer {test_token}")
        print(f"\nExample usage:")
        print(f"curl -H 'Authorization: Bearer {test_token}' {BACKEND_URL}/auth/me")
        return
    
    print("\n❌ Existing test token is invalid or expired.")
    
    # Check if backend is accessible
    try:
        response = requests.get(f"{BACKEND_URL}/docs")
        if response.status_code == 200:
            print("✅ Backend is accessible")
        else:
            print(f"❌ Backend returned status: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Make sure the backend is running with: docker-compose up backend")
        return
    
    print("\n2. To get a new token, you need to:")
    print("   a) Complete the Google OAuth flow")
    print("   b) Get the authorization code from the callback")
    print("   c) Exchange it for a token")
    
    print(f"\n📱 Google OAuth URL:")
    print(f"{get_google_oauth_url()}")
    
    print("\n3. Alternative: Check your .env file for JWT_SECRET_KEY and create a test token manually")
    print("   You can use the debug_auth.py script as a reference")

if __name__ == "__main__":
    main()
