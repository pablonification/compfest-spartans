#!/usr/bin/env python3
"""
Script to generate a valid bearer token for testing the SmartBin API
"""

import jwt
from datetime import datetime, timedelta, timezone

# Configuration from your environment
JWT_SECRET_KEY = "551265b057390be3973f3acaf86341483e6cf87ff804da221071c806a8097054"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days

def create_test_token():
    """Create a JWT token for the existing test user"""
    
    # User data from the database - use the _id field, not the id field
    user_data = {
        "sub": "68a1a8306617ece535d3467c",  # This is the _id from the database
        "email": "arqilasp@gmail.com"
    }
    
    # Set expiration
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    user_data.update({"exp": expire})
    
    # Create token
    token = jwt.encode(user_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return token

def main():
    print("🔑 SmartBin Test Token Generator")
    print("=" * 40)
    
    try:
        # Generate token
        token = create_test_token()
        
        print(f"✅ Generated valid bearer token!")
        print(f"\n🎯 Use this bearer token for testing:")
        print(f"Bearer {token}")
        
        print(f"\n📋 Token details:")
        print(f"   User ID (_id): 68a1a8306617ece535d3467c")
        print(f"   Email: arqilasp@gmail.com")
        print(f"   Expires: {datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)}")
        
        print(f"\n🚀 Example usage:")
        print(f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/auth/me")
        
        print(f"\n📝 Copy this token to your test scripts or API clients")
        
    except Exception as e:
        print(f"❌ Error generating token: {e}")

if __name__ == "__main__":
    main()
