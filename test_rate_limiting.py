import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import tempfile
import os

from main import app, get_db, log_login_attempt, is_user_blocked, get_block_remaining_time
from database import Base
from models import User, LoginAttempt
from auth import get_password_hash


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestLoginAttemptLogging:
    """Test login attempt logging functionality"""
    
    def test_log_successful_login(self, db_session):
        """Test logging a successful login attempt"""
        log_login_attempt(db_session, "testuser", "127.0.0.1", True)
        
        attempt = db_session.query(LoginAttempt).filter_by(username="testuser").first()
        assert attempt is not None
        assert attempt.username == "testuser"
        assert attempt.ip_address == "127.0.0.1"
        assert attempt.success == 1
        assert attempt.timestamp is not None
    
    def test_log_failed_login(self, db_session):
        """Test logging a failed login attempt"""
        log_login_attempt(db_session, "testuser", "127.0.0.1", False)
        
        attempt = db_session.query(LoginAttempt).filter_by(username="testuser").first()
        assert attempt is not None
        assert attempt.username == "testuser"
        assert attempt.ip_address == "127.0.0.1"
        assert attempt.success == 0
        assert attempt.timestamp is not None
    
    def test_log_multiple_attempts(self, db_session):
        """Test logging multiple login attempts"""
        for i in range(3):
            log_login_attempt(db_session, "testuser", "127.0.0.1", False)
        
        attempts = db_session.query(LoginAttempt).filter_by(username="testuser").all()
        assert len(attempts) == 3
        assert all(attempt.success == 0 for attempt in attempts)


class TestUserBlocking:
    """Test user blocking functionality"""
    
    def test_user_not_blocked_initially(self, db_session):
        """Test that a user is not blocked initially"""
        assert not is_user_blocked(db_session, "testuser")
    
    def test_user_not_blocked_with_few_attempts(self, db_session):
        """Test that a user is not blocked with less than 5 failed attempts"""
        for i in range(4):
            log_login_attempt(db_session, "testuser", "127.0.0.1", False)
        
        assert not is_user_blocked(db_session, "testuser")
    
    def test_user_blocked_after_5_attempts(self, db_session):
        """Test that a user is blocked after 5 failed attempts within 1 minute"""
        current_time = datetime.utcnow()
        
        # Create 5 failed attempts within the last minute
        for i in range(5):
            attempt = LoginAttempt(
                username="testuser",
                ip_address="127.0.0.1",
                success=0,
                timestamp=current_time - timedelta(seconds=10*i)
            )
            db_session.add(attempt)
        db_session.commit()
        
        assert is_user_blocked(db_session, "testuser")
    
    def test_user_not_blocked_old_attempts(self, db_session):
        """Test that a user is not blocked if failed attempts are older than 1 minute"""
        old_time = datetime.utcnow() - timedelta(minutes=2)
        
        # Create 5 failed attempts older than 1 minute
        for i in range(5):
            attempt = LoginAttempt(
                username="testuser",
                ip_address="127.0.0.1",
                success=0,
                timestamp=old_time - timedelta(seconds=10*i)
            )
            db_session.add(attempt)
        db_session.commit()
        
        assert not is_user_blocked(db_session, "testuser")
    
    def test_user_not_blocked_after_30_minutes(self, db_session):
        """Test that a user is not blocked after 30 minutes have passed"""
        old_time = datetime.utcnow() - timedelta(minutes=31)
        
        # Create 5 failed attempts 31 minutes ago
        for i in range(5):
            attempt = LoginAttempt(
                username="testuser",
                ip_address="127.0.0.1",
                success=0,
                timestamp=old_time - timedelta(seconds=10*i)
            )
            db_session.add(attempt)
        db_session.commit()
        
        assert not is_user_blocked(db_session, "testuser")
    
    def test_successful_attempt_doesnt_count(self, db_session):
        """Test that successful attempts don't count towards blocking"""
        current_time = datetime.utcnow()
        
        # Create 4 failed attempts and 1 successful attempt
        for i in range(4):
            attempt = LoginAttempt(
                username="testuser",
                ip_address="127.0.0.1",
                success=0,
                timestamp=current_time - timedelta(seconds=10*i)
            )
            db_session.add(attempt)
        
        # Add successful attempt
        success_attempt = LoginAttempt(
            username="testuser",
            ip_address="127.0.0.1",
            success=1,
            timestamp=current_time - timedelta(seconds=50)
        )
        db_session.add(success_attempt)
        db_session.commit()
        
        assert not is_user_blocked(db_session, "testuser")


class TestBlockRemainingTime:
    """Test block remaining time calculation"""
    
    def test_remaining_time_calculation(self, db_session):
        """Test calculation of remaining block time"""
        current_time = datetime.utcnow()
        
        # Create 5 failed attempts within the last minute
        for i in range(5):
            attempt = LoginAttempt(
                username="testuser",
                ip_address="127.0.0.1",
                success=0,
                timestamp=current_time - timedelta(seconds=10*i)
            )
            db_session.add(attempt)
        db_session.commit()
        
        remaining = get_block_remaining_time(db_session, "testuser")
        # Should be close to 30 minutes (1800 seconds), allow some tolerance
        assert 1790 <= remaining <= 1800
    
    def test_no_remaining_time_if_not_blocked(self, db_session):
        """Test that remaining time is 0 if user is not blocked"""
        remaining = get_block_remaining_time(db_session, "testuser")
        assert remaining == 0
    
    def test_remaining_time_decreases(self, db_session):
        """Test that remaining time decreases over time"""
        past_time = datetime.utcnow() - timedelta(minutes=5)
        
        # Create 5 failed attempts 5 minutes ago
        for i in range(5):
            attempt = LoginAttempt(
                username="testuser",
                ip_address="127.0.0.1",
                success=0,
                timestamp=past_time - timedelta(seconds=10*i)
            )
            db_session.add(attempt)
        db_session.commit()
        
        remaining = get_block_remaining_time(db_session, "testuser")
        # Should be approximately 25 minutes (1500 seconds)
        assert 1490 <= remaining <= 1510


class TestLoginEndpoint:
    """Test login endpoint with rate limiting"""
    
    def test_successful_login(self, client, test_user):
        """Test successful login"""
        response = client.post("/login", data={
            "username": "testuser",
            "password": "testpassword"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_failed_login_wrong_password(self, client, test_user):
        """Test failed login with wrong password"""
        response = client.post("/login", data={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"
    
    def test_failed_login_nonexistent_user(self, client):
        """Test failed login with nonexistent user"""
        response = client.post("/login", data={
            "username": "nonexistent",
            "password": "anypassword"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"
    
    def test_rate_limiting_after_5_attempts(self, client, test_user):
        """Test that user is blocked after 5 failed login attempts"""
        # Make 5 failed attempts
        for i in range(5):
            response = client.post("/login", data={
                "username": "testuser",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
        
        # 6th attempt should be blocked
        response = client.post("/login", data={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 429
        assert "temporarily blocked" in response.json()["detail"]
    
    def test_successful_login_after_failed_attempts(self, client, test_user):
        """Test that successful login is still possible after some failed attempts"""
        # Make 4 failed attempts
        for i in range(4):
            response = client.post("/login", data={
                "username": "testuser",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
        
        # 5th attempt with correct password should succeed
        response = client.post("/login", data={
            "username": "testuser",
            "password": "testpassword"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_blocked_user_correct_password(self, client, test_user):
        """Test that even correct password is blocked when user is blocked"""
        # Make 5 failed attempts
        for i in range(5):
            response = client.post("/login", data={
                "username": "testuser",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
        
        # Try with correct password - should still be blocked
        response = client.post("/login", data={
            "username": "testuser",
            "password": "testpassword"
        })
        assert response.status_code == 429
        assert "temporarily blocked" in response.json()["detail"]


class TestTokenEndpoint:
    """Test token endpoint with rate limiting"""
    
    def test_successful_token_request(self, client, test_user):
        """Test successful token request"""
        response = client.post("/token", data={
            "username": "testuser",
            "password": "testpassword"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_token_rate_limiting(self, client, test_user):
        """Test that token endpoint also implements rate limiting"""
        # Make 5 failed attempts
        for i in range(5):
            response = client.post("/token", data={
                "username": "testuser",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
        
        # 6th attempt should be blocked
        response = client.post("/token", data={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 429
        assert "temporarily blocked" in response.json()["detail"]


class TestRateLimitingIntegration:
    """Integration tests for rate limiting across endpoints"""
    
    def test_rate_limiting_shared_across_endpoints(self, client, test_user):
        """Test that rate limiting is shared between login and token endpoints"""
        # Make 3 failed attempts on login endpoint
        for i in range(3):
            response = client.post("/login", data={
                "username": "testuser",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
        
        # Make 2 failed attempts on token endpoint
        for i in range(2):
            response = client.post("/token", data={
                "username": "testuser",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
        
        # Next attempt on either endpoint should be blocked
        response = client.post("/login", data={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 429
        
        response = client.post("/token", data={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 429
    
    def test_different_users_independent_limits(self, client, db_session):
        """Test that different users have independent rate limits"""
        # Create two test users
        user1 = User(
            username="user1",
            email="user1@example.com",
            hashed_password=get_password_hash("password1")
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            hashed_password=get_password_hash("password2")
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        
        # Make 5 failed attempts for user1
        for i in range(5):
            response = client.post("/login", data={
                "username": "user1",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
        
        # user1 should be blocked
        response = client.post("/login", data={
            "username": "user1",
            "password": "wrongpassword"
        })
        assert response.status_code == 429
        
        # user2 should still be able to login
        response = client.post("/login", data={
            "username": "user2",
            "password": "password2"
        })
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])