#!/usr/bin/env python3
"""
Test script to check scan endpoint functionality
"""

import requests
import json
import os

def test_scan_endpoint():
    """Test the scan endpoint with a simple GET request to see if it's accessible"""
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if endpoint exists
    print("🔍 Testing scan endpoint accessibility...")
    try:
        response = requests.get(f"{base_url}/scan")
        print(f"GET /scan response: {response.status_code}")
        if response.status_code == 405:  # Method Not Allowed is expected for GET
            print("✅ Endpoint exists (GET not allowed, which is correct)")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error accessing scan endpoint: {e}")
    
    # Test 2: Check if we can access the endpoint with OPTIONS
    print("\n🔍 Testing scan endpoint with OPTIONS...")
    try:
        response = requests.options(f"{base_url}/scan")
        print(f"OPTIONS /scan response: {response.status_code}")
        print(f"Allowed methods: {response.headers.get('Allow', 'Unknown')}")
    except Exception as e:
        print(f"❌ Error with OPTIONS request: {e}")
    
    # Test 3: Check if we can access the endpoint with POST (without image)
    print("\n🔍 Testing scan endpoint with POST (no image)...")
    try:
        response = requests.post(f"{base_url}/scan")
        print(f"POST /scan response: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error with POST request: {e}")
    
    # Test 4: Check available endpoints
    print("\n🔍 Checking available endpoints...")
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"Docs endpoint: {response.status_code}")
        if response.status_code == 200:
            print("✅ API documentation available at /docs")
    except Exception as e:
        print(f"❌ Error accessing docs: {e}")
    
    # Test 5: Check environment variables
    print("\n🔍 Checking environment variables...")
    env_vars = [
        "ROBOFLOW_API_KEY",
        "MONGODB_URI", 
        "MONGODB_DB_NAME",
        "JWT_SECRET_KEY"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (set)")
        else:
            print(f"❌ {var}: Not set")

if __name__ == "__main__":
    test_scan_endpoint()

