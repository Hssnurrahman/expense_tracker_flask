# Expense Tracker API

A comprehensive FastAPI-based Expense Tracker API with advanced security features including rate limiting, JWT authentication, and comprehensive expense management capabilities.

## 🚀 Features

### Core Functionality
- **User Management** - Secure registration and authentication system
- **Expense Tracking** - Complete CRUD operations for personal expenses
- **Category Management** - Organize expenses with custom categories
- **Data Isolation** - Users can only access their own data

### Advanced Security
- **Rate Limiting** - Automatic blocking after 5 failed login attempts within 1 minute
- **Account Lockout** - 30-minute temporary blocking for enhanced security
- **IP Address Logging** - Security monitoring and audit trail
- **JWT Authentication** - Token-based authentication with 24-hour expiration
- **Password Security** - bcrypt hashing with secure salt rounds

### API Features
- **Interactive Documentation** - Built-in Swagger UI and ReDoc
- **Request Validation** - Pydantic models for robust data validation
- **Database Support** - PostgreSQL (primary), SQLite (testing), Supabase integration
- **CORS Support** - Configured for web application integration
- **Comprehensive Error Handling** - Detailed error messages with proper HTTP status codes

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL (for production) or SQLite (for development)
- pip (Python package manager)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd expense-tracker-api
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up database:**
   ```bash
   # Create all tables
   python create_tables.py
   
   # Or reset database (WARNING: Deletes all data)
   python quick_reset.py
   ```

## 🚀 Running the Application

### Development Server
```bash
python main.py
```
or
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Production Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Once the server is running, access the interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc  
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔗 API Endpoints

### 🏠 Root
- `GET /` - Welcome message and API status

### 🔐 Authentication
- `POST /signup` - Register a new user account
- `POST /login` - User login with rate limiting protection
- `POST /token` - OAuth2-compatible token endpoint

### 👤 Users
- `GET /users/me/` - Get current user profile information

### 🏷️ Categories
- `POST /categories/` - Create a new expense category
- `GET /categories/` - List all categories for current user (with pagination)

### 💰 Expenses
- `POST /expenses/` - Create a new expense
- `GET /expenses/` - List all expenses for current user (with pagination)
- `GET /expenses/{expense_id}` - Get specific expense details
- `PUT /expenses/{expense_id}` - Update an existing expense
- `DELETE /expenses/{expense_id}` - Delete an expense

## 📝 Example Usage

### 1. User Registration
```bash
curl -X POST "http://localhost:8000/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john.doe@example.com",
    "password": "securepassword123"
  }'
```

### 2. User Login
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=securepassword123"
```

### 3. Create Category (with token)
```bash
curl -X POST "http://localhost:8000/categories/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Food & Dining",
    "description": "Restaurant meals and food purchases"
  }'
```

### 4. Create Expense (with token)
```bash
curl -X POST "http://localhost:8000/expenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "amount": 29.99,
    "description": "Lunch at restaurant",
    "date": "2024-01-15",
    "category_id": 1
  }'
```

### 5. List Expenses (with pagination)
```bash
curl -X GET "http://localhost:8000/expenses/?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔒 Security Features

### Rate Limiting
- **Threshold**: 5 failed login attempts within 1 minute
- **Block Duration**: 30 minutes
- **Scope**: Per username across all authentication endpoints
- **Monitoring**: IP address logging for security analysis

### Authentication Flow
1. User registers with email, username, and password
2. Password is securely hashed using bcrypt
3. Login returns JWT token with 24-hour expiration
4. Token must be included in Authorization header for protected endpoints

### Error Responses
- **200** - Success
- **201** - Created
- **400** - Bad Request (validation error, duplicate user)
- **401** - Unauthorized (invalid credentials)
- **403** - Forbidden (insufficient permissions)
- **429** - Too Many Requests (rate limited)
- **500** - Internal Server Error

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/expense_tracker
# Alternative for SQLite: sqlite:///./expense_tracker.db

# Supabase (optional)
SUPABASE_DATABASE_URL=postgresql://username:password@host:port/database
```

### Database Setup

#### PostgreSQL (Recommended)
```bash
# Install PostgreSQL and create database
createdb expense_tracker

# Run table creation
python create_tables.py
```

#### SQLite (Development)
```bash
# Tables will be created automatically
python main.py
```

## 🧪 Testing

### Run Rate Limiting Tests
```bash
# Comprehensive test suite
python -m pytest test_rate_limiting.py -v

# Simple standalone tests  
python test_rate_limiting_simple.py

# Manual testing
python manual_test_rate_limiting.py
```

### Run Signup Tests
```bash
python test_signup.py
```

### Database Management
```bash
# Verify tables exist
python verify_tables.py

# Reset all tables (WARNING: Deletes all data)
python recreate_tables.py

# Quick reset without prompts
python quick_reset.py
```

## 🗄️ Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email address
- `hashed_password` - bcrypt hashed password

### Categories Table  
- `id` - Primary key
- `name` - Category name
- `description` - Optional description
- `owner_id` - Foreign key to users

### Expenses Table
- `id` - Primary key
- `amount` - Expense amount (decimal)
- `description` - Optional description
- `date` - Expense date
- `category_id` - Foreign key to categories (optional)
- `owner_id` - Foreign key to users

### Login Attempts Table (Security)
- `id` - Primary key
- `username` - Username attempted
- `ip_address` - Client IP address
- `success` - Success flag (0=failed, 1=success)
- `timestamp` - Attempt timestamp

## 🔧 Development Tools

### Database Management Scripts
- `create_tables.py` - Initialize database schema
- `recreate_tables.py` - Reset database with confirmation
- `quick_reset.py` - Fast database reset
- `verify_tables.py` - Verify table structure

### Testing Scripts
- `test_rate_limiting.py` - Comprehensive rate limiting tests
- `test_signup.py` - User registration tests
- `manual_test_rate_limiting.py` - Manual testing interface

## 🏗️ Architecture

### Project Structure
```
expense-tracker-api/
├── main.py                    # FastAPI application
├── models.py                  # SQLAlchemy database models
├── schemas.py                 # Pydantic request/response models
├── crud.py                    # Database operations
├── auth.py                    # Authentication functions
├── database.py                # Database configuration
├── requirements.txt           # Python dependencies
├── test_*.py                  # Test files
├── create_*.py               # Database management scripts
└── README.md                 # This file
```

### Key Technologies
- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and serialization
- **JWT** - JSON Web Tokens for authentication
- **bcrypt** - Password hashing
- **PostgreSQL** - Primary database
- **pytest** - Testing framework

## 📊 Monitoring and Logging

### Security Monitoring
- All login attempts logged with IP addresses
- Failed login attempt tracking
- Rate limiting status and remaining time
- User blocking and unblocking events

### Query Examples
```sql
-- Check recent failed login attempts
SELECT * FROM login_attempts 
WHERE success = 0 AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;

-- Monitor rate limiting blocks
SELECT username, COUNT(*) as failed_attempts, MAX(timestamp) as last_attempt
FROM login_attempts 
WHERE success = 0 AND timestamp > NOW() - INTERVAL '1 day'
GROUP BY username
HAVING COUNT(*) >= 5;
```

## 🚀 Deployment

### Production Checklist
- [ ] Set strong SECRET_KEY in environment variables
- [ ] Configure PostgreSQL database
- [ ] Set up proper logging
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL/TLS certificates
- [ ] Configure monitoring and alerting
- [ ] Set up database backups
- [ ] Review rate limiting thresholds

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
1. Check the interactive API documentation at `/docs`
2. Review the test files for usage examples
3. Check the database with `verify_tables.py`
4. Review logs for error details

---

**Built with ❤️ using FastAPI**