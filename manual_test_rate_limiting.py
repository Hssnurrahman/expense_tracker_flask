#!/usr/bin/env python3
"""
Manual test script for rate limiting functionality
Tests the rate limiting without requiring pytest
"""

import requests
import time
import json
from datetime import datetime, timedelta
import sqlite3
import os


def create_test_database():
    """Create a test database and user"""
    # Remove existing test database
    if os.path.exists("test_manual.db"):
        os.remove("test_manual.db")
    
    # Create database schema
    conn = sqlite3.connect("test_manual.db")
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            hashed_password TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE login_attempts (
            id INTEGER PRIMARY KEY,
            username TEXT,
            ip_address TEXT,
            success INTEGER DEFAULT 0,
            timestamp DATETIME
        )
    ''')
    
    # Insert test user (password hash for "testpassword")
    cursor.execute('''
        INSERT INTO users (username, email, hashed_password) 
        VALUES (?, ?, ?)
    ''', ("testuser", "test@example.com", "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"))
    
    conn.commit()
    conn.close()
    print("✅ Test database created with test user")


def test_successful_login():
    """Test successful login"""
    print("\n🔍 Testing successful login...")
    
    response = requests.post("http://localhost:8000/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    
    if response.status_code == 200:
        print("✅ Successful login test passed")
        return True
    else:
        print(f"❌ Successful login test failed: {response.status_code} - {response.text}")
        return False


def test_failed_login():
    """Test failed login"""
    print("\n🔍 Testing failed login...")
    
    response = requests.post("http://localhost:8000/login", data={
        "username": "testuser",
        "password": "wrongpassword"
    })
    
    if response.status_code == 401:
        print("✅ Failed login test passed")
        return True
    else:
        print(f"❌ Failed login test failed: {response.status_code} - {response.text}")
        return False


def test_rate_limiting():
    """Test rate limiting after 5 failed attempts"""
    print("\n🔍 Testing rate limiting (5 failed attempts)...")
    
    # Make 5 failed attempts
    for i in range(5):
        response = requests.post("http://localhost:8000/login", data={
            "username": "testuser",
            "password": "wrongpassword"
        })
        print(f"  Attempt {i+1}: {response.status_code}")
        
        if response.status_code != 401:
            print(f"❌ Expected 401, got {response.status_code}")
            return False
    
    # 6th attempt should be blocked
    response = requests.post("http://localhost:8000/login", data={
        "username": "testuser",
        "password": "wrongpassword"
    })
    
    if response.status_code == 429:
        print("✅ Rate limiting test passed - user blocked after 5 attempts")
        print(f"  Block message: {response.json().get('detail', 'No detail')}")
        return True
    else:
        print(f"❌ Rate limiting test failed: Expected 429, got {response.status_code}")
        return False


def test_blocked_with_correct_password():
    """Test that even correct password is blocked when user is blocked"""
    print("\n🔍 Testing blocked user with correct password...")
    
    response = requests.post("http://localhost:8000/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    
    if response.status_code == 429:
        print("✅ Blocked user test passed - correct password still blocked")
        return True
    else:
        print(f"❌ Blocked user test failed: Expected 429, got {response.status_code}")
        return False


def test_token_endpoint_rate_limiting():
    """Test that token endpoint also implements rate limiting"""
    print("\n🔍 Testing token endpoint rate limiting...")
    
    response = requests.post("http://localhost:8000/token", data={
        "username": "testuser",
        "password": "wrongpassword"
    })
    
    if response.status_code == 429:
        print("✅ Token endpoint rate limiting test passed")
        return True
    else:
        print(f"❌ Token endpoint rate limiting test failed: Expected 429, got {response.status_code}")
        return False


def check_database_entries():
    """Check that login attempts are properly logged in database"""
    print("\n🔍 Checking database entries...")
    
    conn = sqlite3.connect("test_manual.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM login_attempts WHERE username = 'testuser'")
    total_attempts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM login_attempts WHERE username = 'testuser' AND success = 0")
    failed_attempts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM login_attempts WHERE username = 'testuser' AND success = 1")
    successful_attempts = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"  Total attempts logged: {total_attempts}")
    print(f"  Failed attempts: {failed_attempts}")
    print(f"  Successful attempts: {successful_attempts}")
    
    if total_attempts > 0:
        print("✅ Database logging test passed")
        return True
    else:
        print("❌ Database logging test failed")
        return False


def main():
    """Run all manual tests"""
    print("🧪 Manual Rate Limiting Tests")
    print("=" * 50)
    
    # Note: This test assumes the server is running on localhost:8000
    # You need to start the server with: python main.py
    
    print("📝 Note: Make sure the server is running on localhost:8000")
    print("   Start with: python main.py")
    print("   (You may need to modify database.py to use SQLite for testing)")
    
    input("Press Enter to continue with tests...")
    
    # Create test database
    create_test_database()
    
    # Run tests
    tests = [
        test_successful_login,
        test_failed_login,
        test_rate_limiting,
        test_blocked_with_correct_password,
        test_token_endpoint_rate_limiting,
        check_database_entries
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    
    # Cleanup
    if os.path.exists("test_manual.db"):
        os.remove("test_manual.db")
        print("🧹 Test database cleaned up")


if __name__ == "__main__":
    main()