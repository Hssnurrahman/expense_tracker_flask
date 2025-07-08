# Expense Tracker API

A FastAPI-based Expense Tracker API that allows users to track their expenses and manage categories.

## Features

- User authentication with JWT tokens
- Create, read, update, and delete expenses
- Manage expense categories
- Secure endpoints with authentication
- SQLite database (can be easily switched to PostgreSQL/MySQL)
- Pydantic models for request/response validation

## Prerequisites

- Python 3.7+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd expense-tracker-api
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the FastAPI development server:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

## API Documentation

Once the server is running, you can access:

- Interactive API docs: http://127.0.0.1:8000/docs
- Alternative API docs: http://127.0.0.1:8000/redoc

## API Endpoints

### Authentication

- `POST /token` - Get access token (use form-data with username and password)

### Users

- `POST /users/` - Create a new user
- `GET /users/me/` - Get current user details

### Categories

- `POST /categories/` - Create a new category
- `GET /categories/` - List all categories for the current user

### Expenses

- `POST /expenses/` - Create a new expense
- `GET /expenses/` - List all expenses for the current user
- `GET /expenses/{expense_id}` - Get a specific expense
- `PUT /expenses/{expense_id}` - Update an expense
- `DELETE /expenses/{expense_id}` - Delete an expense

## Example Usage

1. First, create a user:
   ```bash
   curl -X 'POST' \
     'http://127.0.0.1:8000/users/' \
     -H 'Content-Type: application/json' \
     -d '{
       "email": "user@example.com",
       "username": "testuser",
       "password": "testpassword"
     }'
   ```

2. Get an access token:
   ```bash
   curl -X 'POST' \
     'http://127.0.0.1:8000/token' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'username=testuser&password=testpassword'
   ```

3. Use the token to access protected endpoints:
   ```bash
   curl -X 'GET' \
     'http://127.0.0.1:8000/expenses/' \
     -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
   ```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./expense_tracker.db
```

## Running Tests

To run the test suite:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
