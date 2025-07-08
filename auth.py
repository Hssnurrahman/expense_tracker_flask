from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import os
from dotenv import load_dotenv
import models, schemas
from database import get_db

# Load environment variables
load_dotenv()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Update OAuth2 scheme to use the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# User authentication functions
def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    now = datetime.utcnow()
    
    # Set default expiration to 24 hours if not specified
    if expires_delta is None:
        expires_delta = timedelta(hours=24)
    
    expire = now + expires_delta
    
    # Debug logging
    print(f"Creating token with expiration: {expire} (in {expires_delta})")
    
    # Use integer timestamp for JWT standard compatibility
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp())  # Not Before time - valid from now
    })

    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        print(f"Error encoding JWT: {e}")
        raise

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Add better error handling for token decoding
        try:
            print(f"Attempting to decode token: {token[:20]}...")
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"require": ["exp", "sub"]}  # Ensure required claims are present
            )
            print(f"Decoded token payload: {payload}")
        except JWTError as e:
            print(f"JWT decode error: {str(e)}")
            print(f"Token: {token}")
            print(f"SECRET_KEY: {SECRET_KEY}")
            print(f"ALGORITHM: {ALGORITHM}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        username: str = payload.get("sub")
        if not username:
            print("Error: No 'sub' claim in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: Missing 'sub' claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = schemas.TokenData(username=username)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected authentication error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication"
        )

    # Get user from database
    user = get_user(db, username=token_data.username)
    if user is None:
        print(f"User not found in database: {token_data.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    # All users are considered active since we don't have is_active field
    return current_user