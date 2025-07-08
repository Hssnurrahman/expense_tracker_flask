#!/usr/bin/env python3
"""
Test script to verify signup endpoint works
"""

import requests
import json

def test_signup():
    """Test the signup endpoint"""
    
    url = "http://localhost:8000/signup"
    
    # Test data
    user_data = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "password": "testpassword123"
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing signup endpoint...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(user_data, indent=2)}")
    print(f"Headers: {headers}")
    
    try:
        # Make the request
        response = requests.post(url, json=user_data, headers=headers)
        
        print(f"\n📊 Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content: {response.text}")
        
        if response.status_code == 200:
            print("✅ Signup successful!")
            return True
        else:
            print("❌ Signup failed!")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_signup()