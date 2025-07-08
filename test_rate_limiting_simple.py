#!/usr/bin/env python3
"""
Simple test for rate limiting functionality
Tests the core rate limiting logic without requiring external dependencies
"""

import sys
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock SQLAlchemy components
class MockQuery:
    def __init__(self, results):
        self.results = results
        self.filters = []
        self.order_by_clause = None
        self.limit_value = None
    
    def filter(self, *args):
        self.filters.extend(args)
        return self
    
    def filter_by(self, **kwargs):
        self.filters.append(kwargs)
        return self
    
    def order_by(self, clause):
        self.order_by_clause = clause
        return self
    
    def limit(self, value):
        self.limit_value = value
        return self
    
    def count(self):
        return len(self.results)
    
    def first(self):
        return self.results[0] if self.results else None
    
    def all(self):
        return self.results

class MockLoginAttempt:
    def __init__(self, username, ip_address, success, timestamp):
        self.username = username
        self.ip_address = ip_address
        self.success = success
        self.timestamp = timestamp

class MockSession:
    def __init__(self):
        self.login_attempts = []
        self.committed = False
    
    def query(self, model):
        return MockQuery(self.login_attempts)
    
    def add(self, obj):
        self.login_attempts.append(obj)
    
    def commit(self):
        self.committed = True

# Import the functions we want to test
from main import log_login_attempt, is_user_blocked, get_block_remaining_time


def test_log_login_attempt():
    """Test logging login attempts"""
    print("Testing log_login_attempt...")
    
    # Create mock database session
    db = MockSession()
    
    # Test logging a failed attempt
    log_login_attempt(db, "testuser", "127.0.0.1", False)
    
    # Verify attempt was logged
    assert len(db.login_attempts) == 1
    assert db.login_attempts[0].username == "testuser"
    assert db.login_attempts[0].ip_address == "127.0.0.1"
    assert db.login_attempts[0].success == 0
    assert db.committed == True
    
    print("✅ log_login_attempt test passed")


def test_is_user_blocked_not_blocked():
    """Test user not blocked with few attempts"""
    print("Testing is_user_blocked (not blocked)...")
    
    # Create mock database session with 4 failed attempts
    db = MockSession()
    current_time = datetime.utcnow()
    
    for i in range(4):
        attempt = MockLoginAttempt(
            username="testuser",
            ip_address="127.0.0.1",
            success=0,
            timestamp=current_time - timedelta(seconds=10*i)
        )
        db.login_attempts.append(attempt)
    
    # Mock the query method to return our attempts
    original_query = db.query
    def mock_query(model):
        query = original_query(model)
        # Filter by username and failed attempts
        filtered_attempts = [a for a in db.login_attempts 
                           if a.username == "testuser" and a.success == 0]
        query.results = filtered_attempts
        return query
    
    db.query = mock_query
    
    # User should not be blocked with only 4 attempts
    result = is_user_blocked(db, "testuser")
    assert result == False
    
    print("✅ is_user_blocked (not blocked) test passed")


def test_is_user_blocked_blocked():
    """Test user blocked with 5 attempts"""
    print("Testing is_user_blocked (blocked)...")
    
    # Create mock database session with 5 failed attempts
    db = MockSession()
    current_time = datetime.utcnow()
    
    for i in range(5):
        attempt = MockLoginAttempt(
            username="testuser",
            ip_address="127.0.0.1",
            success=0,
            timestamp=current_time - timedelta(seconds=10*i)
        )
        db.login_attempts.append(attempt)
    
    # Mock the query method to return our attempts
    original_query = db.query
    def mock_query(model):
        query = MockQuery([])
        
        # First call: count recent failed attempts
        if not hasattr(query, 'count_called'):
            query.count_called = True
            filtered_attempts = [a for a in db.login_attempts 
                               if a.username == "testuser" and a.success == 0]
            query.results = filtered_attempts
            original_count = query.count
            query.count = lambda: 5  # Return 5 failed attempts
        
        # Second call: get the 5th attempt
        else:
            filtered_attempts = [a for a in db.login_attempts 
                               if a.username == "testuser" and a.success == 0]
            query.results = filtered_attempts
        
        return query
    
    db.query = mock_query
    
    # User should be blocked with 5 attempts
    result = is_user_blocked(db, "testuser")
    assert result == True
    
    print("✅ is_user_blocked (blocked) test passed")


def test_get_block_remaining_time():
    """Test remaining block time calculation"""
    print("Testing get_block_remaining_time...")
    
    # Create mock database session
    db = MockSession()
    current_time = datetime.utcnow()
    
    # Add a failed attempt from 5 minutes ago
    attempt = MockLoginAttempt(
        username="testuser",
        ip_address="127.0.0.1",
        success=0,
        timestamp=current_time - timedelta(minutes=5)
    )
    db.login_attempts.append(attempt)
    
    # Mock the query method
    def mock_query(model):
        query = MockQuery([attempt])
        return query
    
    db.query = mock_query
    
    # Should return approximately 25 minutes (1500 seconds)
    remaining = get_block_remaining_time(db, "testuser")
    expected = 25 * 60  # 25 minutes in seconds
    
    # Allow some tolerance for execution time
    assert abs(remaining - expected) < 60, f"Expected ~{expected}, got {remaining}"
    
    print("✅ get_block_remaining_time test passed")


def test_no_block_remaining_time():
    """Test no remaining time when user not blocked"""
    print("Testing get_block_remaining_time (no block)...")
    
    # Create mock database session with no attempts
    db = MockSession()
    
    # Mock the query method to return no attempts
    def mock_query(model):
        query = MockQuery([])
        return query
    
    db.query = mock_query
    
    # Should return 0 when no blocking attempts
    remaining = get_block_remaining_time(db, "testuser")
    assert remaining == 0
    
    print("✅ get_block_remaining_time (no block) test passed")


def run_all_tests():
    """Run all tests"""
    print("🧪 Running Simple Rate Limiting Tests")
    print("=" * 50)
    
    tests = [
        test_log_login_attempt,
        test_is_user_blocked_not_blocked,
        test_is_user_blocked_blocked,
        test_get_block_remaining_time,
        test_no_block_remaining_time,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)