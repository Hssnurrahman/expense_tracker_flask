from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import models, schemas, crud
from database import SessionLocal, engine
from datetime import timedelta, datetime
import logging
from auth import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expense Tracker API",
    description="""
    A comprehensive expense tracking API with advanced security features.
    
    ## Features
    
    * **User Management**: Registration, authentication with JWT tokens
    * **Expense Tracking**: Full CRUD operations for expenses
    * **Category Management**: Organize expenses by categories
    * **Security**: Rate limiting, brute force protection, IP logging
    * **Authentication**: JWT-based with 24-hour token expiration
    
    ## Security
    
    * Rate limiting: 5 failed attempts = 30-minute block
    * IP address logging for security monitoring
    * bcrypt password hashing
    * Resource-level authorization
    """,
    version="1.0.0",
    contact={
        "name": "Expense Tracker API",
        "email": "support@expensetracker.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User registration, login, and token management",
        },
        {
            "name": "Users",
            "description": "User profile management",
        },
        {
            "name": "Categories",
            "description": "Expense category management",
        },
        {
            "name": "Expenses",
            "description": "Expense tracking and management",
        },
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Rate limiting functions
def log_login_attempt(db: Session, username: str, ip_address: str, success: bool):
    """Log a login attempt to the database"""
    login_attempt = models.LoginAttempt(
        username=username,
        ip_address=ip_address,
        success=1 if success else 0,
        timestamp=datetime.utcnow()
    )
    db.add(login_attempt)
    db.commit()


def is_user_blocked(db: Session, username: str) -> bool:
    """Check if user is blocked due to too many failed attempts"""
    # Get failed attempts in the last minute
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    
    failed_attempts = db.query(models.LoginAttempt).filter(
        models.LoginAttempt.username == username,
        models.LoginAttempt.success == 0,
        models.LoginAttempt.timestamp >= one_minute_ago
    ).count()
    
    if failed_attempts >= 5:
        # Check if user is still in 30-minute block period
        thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
        
        # Get the 5th failed attempt (which triggered the block)
        fifth_attempt = db.query(models.LoginAttempt).filter(
            models.LoginAttempt.username == username,
            models.LoginAttempt.success == 0,
            models.LoginAttempt.timestamp >= one_minute_ago
        ).order_by(models.LoginAttempt.timestamp.asc()).limit(1).first()
        
        if fifth_attempt and fifth_attempt.timestamp >= thirty_minutes_ago:
            return True
    
    return False


def get_block_remaining_time(db: Session, username: str) -> int:
    """Get remaining block time in seconds"""
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    
    # Get the 5th failed attempt that triggered the block
    fifth_attempt = db.query(models.LoginAttempt).filter(
        models.LoginAttempt.username == username,
        models.LoginAttempt.success == 0,
        models.LoginAttempt.timestamp >= one_minute_ago
    ).order_by(models.LoginAttempt.timestamp.asc()).limit(1).first()
    
    if fifth_attempt:
        block_end = fifth_attempt.timestamp + timedelta(minutes=30)
        remaining = block_end - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))
    
    return 0


@app.get(
    "/", 
    tags=["Root"],
    summary="Welcome Message",
    description="Returns a welcome message for the API"
)
def read_root():
    """
    Welcome endpoint that confirms the API is running.
    
    Returns a simple welcome message.
    """
    return {"message": "Welcome to Expense Tracker API"}


# Authentication endpoints
@app.post(
    "/signup", 
    response_model=schemas.User,
    tags=["Authentication"],
    summary="User Registration",
    description="Register a new user account",
    status_code=201
)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address (will be unique)
    - **password**: Password (minimum 8 characters recommended)
    
    Returns the created user information (without password).
    
    **Error Cases:**
    - 400: Email already registered
    - 400: Username already taken
    - 500: Server error during user creation
    """
    # Check if user with this email already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Check if username is already taken
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    # Create new user and return the result
    db_user = crud.create_user(db=db, user=user)
    if db_user is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )
    # Return user without hashed_password field
    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username
    )


@app.post(
    "/login", 
    response_model=schemas.Token,
    tags=["Authentication"],
    summary="User Login",
    description="Authenticate user and return access token"
)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.
    
    **Security Features:**
    - Rate limiting: 5 failed attempts within 1 minute = 30-minute block
    - IP address logging for security monitoring
    - Secure password verification with bcrypt
    
    **Request Format:**
    - username: Your username
    - password: Your password
    
    **Returns:**
    - access_token: JWT token (24-hour expiration)
    - token_type: "bearer"
    
    **Error Cases:**
    - 401: Invalid credentials
    - 429: Rate limited (too many failed attempts)
    - 500: Server error
    """
    try:
        # Get client IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if user is blocked due to too many failed attempts
        if is_user_blocked(db, form_data.username):
            remaining_time = get_block_remaining_time(db, form_data.username)
            logger.warning(f"Blocked login attempt for user: {form_data.username} from IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily blocked due to too many failed login attempts. Please try again in {remaining_time // 60} minutes and {remaining_time % 60} seconds.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if username exists
        db_user = crud.get_user_by_username(db, username=form_data.username)
        if not db_user:
            logger.warning(f"Login attempt with non-existent username: {form_data.username} from IP: {client_ip}")
            # Log failed attempt
            log_login_attempt(db, form_data.username, client_ip, False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Authenticate user
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Failed login attempt for user: {form_data.username} from IP: {client_ip}")
            # Log failed attempt
            log_login_attempt(db, form_data.username, client_ip, False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Log successful attempt
        log_login_attempt(db, form_data.username, client_ip, True)

        # Create access token with extended expiration
        access_token_expires = timedelta(hours=24)  # Extend token to 24 hours
        print(f"Creating token for user {user.username} with expiration: {access_token_expires}")
        access_token = create_access_token(
            data={"sub": user.username}, 
            expires_delta=access_token_expires
        )

        logger.info(f"User logged in successfully: {user.username} from IP: {client_ip}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login. Please try again later."
        )


# Keep token endpoint for OAuth compatibility
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    try:
        # Get client IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if user is blocked due to too many failed attempts
        if is_user_blocked(db, form_data.username):
            remaining_time = get_block_remaining_time(db, form_data.username)
            logger.warning(f"Blocked token request for user: {form_data.username} from IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily blocked due to too many failed login attempts. Please try again in {remaining_time // 60} minutes and {remaining_time % 60} seconds.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Failed token request for user: {form_data.username} from IP: {client_ip}")
            # Log failed attempt
            log_login_attempt(db, form_data.username, client_ip, False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Log successful attempt
        log_login_attempt(db, form_data.username, client_ip, True)

        # Use same token expiration as login endpoint (24 hours)
        access_token_expires = timedelta(hours=24)
        print(f"Creating token for OAuth user {user.username} with expiration: {access_token_expires}")
        access_token = create_access_token(
            data={"sub": user.username}, 
            expires_delta=access_token_expires
        )
        logger.info(f"Token created successfully for user: {user.username} from IP: {client_ip}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token creation. Please try again later."
        )


# User endpoints


@app.get(
    "/users/me/", 
    response_model=schemas.User,
    tags=["Users"],
    summary="Get Current User",
    description="Get current user profile information"
)
async def read_users_me(current_user = Depends(get_current_active_user)):
    try:
        # Convert SQLAlchemy model to Pydantic schema
        return schemas.User(
            id=current_user.id,
            email=current_user.email,
            username=current_user.username
        )
    except Exception as e:
        logger.error(f"Error retrieving current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user information"
        )


# Category endpoints
@app.post(
    "/categories/", 
    response_model=schemas.Category, 
    status_code=status.HTTP_201_CREATED,
    tags=["Categories"],
    summary="Create Category",
    description="Create a new expense category"
)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
):
    return crud.create_category(db=db, category=category, user_id=current_user.id)


@app.get(
    "/categories/", 
    response_model=List[schemas.Category],
    tags=["Categories"],
    summary="List Categories",
    description="Get all categories for the current user"
)
def read_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
):
    categories = crud.get_user_categories(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return categories


# Expense endpoints
@app.post(
    "/expenses/", 
    response_model=schemas.Expense, 
    status_code=status.HTTP_201_CREATED,
    tags=["Expenses"],
    summary="Create Expense",
    description="Add a new expense record"
)
def create_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
):
    return crud.create_expense(db=db, expense=expense, user_id=current_user.id)


@app.get(
    "/expenses/", 
    response_model=List[schemas.Expense],
    tags=["Expenses"],
    summary="List Expenses",
    description="Get all expenses for the current user with pagination"
)
def read_expenses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
):
    expenses = crud.get_user_expenses(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return expenses


@app.get("/expenses/{expense_id}", response_model=schemas.Expense)
def read_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
):
    try:
        expense = crud.get_expense(db, expense_id=expense_id)
        if expense is None:
            logger.warning(f"Expense not found: ID {expense_id} requested by user {current_user.username}")
            raise HTTPException(
                status_code=404, 
                detail=f"Expense with ID {expense_id} not found. Please check if the expense exists and you have permission to access it."
            )
        if expense.user_id != current_user.id:
            logger.warning(f"Unauthorized access attempt: User {current_user.username} tried to access expense {expense_id} owned by user {expense.user_id}")
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Expense {expense_id} belongs to another user. You can only access your own expenses."
            )
        return expense
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving expense {expense_id} for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while retrieving expense {expense_id}. Please try again later or contact support if the issue persists."
        )


@app.put("/expenses/{expense_id}", response_model=schemas.Expense)
def update_expense(
    expense_id: int,
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
):
    try:
        db_expense = crud.get_expense(db, expense_id=expense_id)
        if db_expense is None:
            logger.warning(f"Update failed - Expense not found: ID {expense_id} requested by user {current_user.username}")
            raise HTTPException(
                status_code=404, 
                detail=f"Cannot update expense {expense_id} - expense not found. Please verify the expense ID exists."
            )
        if db_expense.user_id != current_user.id:
            logger.warning(f"Update unauthorized: User {current_user.username} tried to update expense {expense_id} owned by user {db_expense.user_id}")
            raise HTTPException(
                status_code=403, 
                detail=f"Update denied. Expense {expense_id} belongs to another user. You can only update your own expenses."
            )
        updated_expense = crud.update_expense(db=db, expense_id=expense_id, expense=expense)
        logger.info(f"Expense {expense_id} successfully updated by user {current_user.username}")
        return updated_expense
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating expense {expense_id} for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while updating expense {expense_id}. Please try again later or contact support if the issue persists."
        )


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
):
    try:
        db_expense = crud.get_expense(db, expense_id=expense_id)
        if db_expense is None:
            logger.warning(f"Delete failed - Expense not found: ID {expense_id} requested by user {current_user.username}")
            raise HTTPException(
                status_code=404, 
                detail=f"Cannot delete expense {expense_id} - expense not found. Please verify the expense ID exists."
            )
        if db_expense.user_id != current_user.id:
            logger.warning(f"Delete unauthorized: User {current_user.username} tried to delete expense {expense_id} owned by user {db_expense.user_id}")
            raise HTTPException(
                status_code=403, 
                detail=f"Delete denied. Expense {expense_id} belongs to another user. You can only delete your own expenses."
            )
        crud.delete_expense(db=db, expense_id=expense_id)
        logger.info(f"Expense {expense_id} successfully deleted by user {current_user.username}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting expense {expense_id} for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while deleting expense {expense_id}. Please try again later or contact support if the issue persists."
        )


# --- TESTS ---
if __name__ == "__main__":
    import uvicorn
    from fastapi.testclient import TestClient
    import random, string

    app_client = TestClient(app)

    def random_str(length=8):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def test_root():
        resp = app_client.get("/")
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_signup_and_login():
        username = "q7b4cwtud1"
        password = "password123"
        email = f"{username}@test.com"
        # Try signup (ignore if already exists)
        resp = app_client.post("/signup", json={"username": username, "email": email, "password": password})
        if resp.status_code not in (200, 400):
            print("Signup failed:", resp.json())
        assert resp.status_code in (200, 400)
        # Login
        resp = app_client.post("/login", data={"username": username, "password": password})
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]
        return token

    def test_user_me(token):
        resp = app_client.get("/users/me/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "username" in resp.json()

    def test_category_crud(token):
        # Create
        cname = "TestCat" + random_str(4)
        resp = app_client.post("/categories/", json={"name": cname}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201, resp.text
        cat = resp.json()
        # List
        resp = app_client.get("/categories/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert any(c["name"] == cname for c in resp.json())

    def test_expense_crud(token):
        # Create category for expense
        cname = "TestCat" + random_str(4)
        resp = app_client.post("/categories/", json={"name": cname}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201, resp.text
        cat_id = resp.json()["id"]
        # Create expense
        exp_data = {"amount": 10.5, "description": "Test expense", "category_id": cat_id}
        resp = app_client.post("/expenses/", json=exp_data, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201, resp.text
        exp = resp.json()
        exp_id = exp["id"]
        # List
        resp = app_client.get("/expenses/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert any(e["id"] == exp_id for e in resp.json())
        # Get single
        resp = app_client.get(f"/expenses/{exp_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        # Update
        new_data = {"amount": 20.0, "description": "Updated expense", "category_id": cat_id}
        resp = app_client.put(f"/expenses/{exp_id}", json=new_data, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        # Delete
        resp = app_client.delete(f"/expenses/{exp_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    # Run all tests
    test_root()
    token = test_signup_and_login()
    test_user_me(token)
    test_category_crud(token)
    test_expense_crud(token)
    print("All route tests passed!")

    uvicorn.run(app, host="0.0.0.0", port=8000)
