#!/usr/bin/env python3
"""
Swagger UI configuration and customization
"""

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def custom_openapi_schema(app: FastAPI):
    """Create custom OpenAPI schema with enhanced documentation"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Expense Tracker API",
        version="1.0.0",
        description="""
        ## 🏦 Expense Tracker API
        
        A comprehensive expense tracking system with enterprise-level security features.
        
        ### 🚀 Key Features
        
        * **User Management** - Secure registration and authentication
        * **Expense Tracking** - Complete CRUD operations for expenses
        * **Category Management** - Organize expenses by custom categories  
        * **Advanced Security** - Rate limiting and brute force protection
        * **JWT Authentication** - Token-based authentication with 24-hour expiration
        
        ### 🔒 Security Features
        
        * **Rate Limiting**: Users blocked after 5 failed login attempts within 1 minute
        * **Account Lockout**: 30-minute temporary blocking period
        * **IP Logging**: All login attempts logged with IP addresses
        * **Password Security**: bcrypt hashing with secure salt rounds
        * **Resource Authorization**: Users can only access their own data
        
        ### 📊 API Usage
        
        1. **Register** a new account via `/signup`
        2. **Login** to get an access token via `/login` 
        3. **Include token** in Authorization header: `Bearer <your-token>`
        4. **Create categories** to organize your expenses
        5. **Add expenses** and assign them to categories
        6. **View/Update/Delete** your expenses and categories
        
        ### 🔧 Development
        
        * **Base URL**: `http://localhost:8000`
        * **Authentication**: JWT Bearer tokens
        * **Rate Limits**: 5 failed attempts = 30-minute block
        * **Token Expiry**: 24 hours
        
        ### 📱 Example Usage
        
        ```bash
        # Register a new user
        curl -X POST "http://localhost:8000/signup" \\
          -H "Content-Type: application/json" \\
          -d '{"username": "john", "email": "john@example.com", "password": "securepass123"}'
        
        # Login and get token
        curl -X POST "http://localhost:8000/login" \\
          -H "Content-Type: application/x-www-form-urlencoded" \\
          -d "username=john&password=securepass123"
        
        # Use token to access protected endpoints
        curl -X GET "http://localhost:8000/users/me/" \\
          -H "Authorization: Bearer <your-token>"
        ```
        
        ### 🏷️ Response Codes
        
        * **200** - Success
        * **201** - Created  
        * **400** - Bad Request (validation error)
        * **401** - Unauthorized (invalid credentials)
        * **403** - Forbidden (insufficient permissions)
        * **429** - Too Many Requests (rate limited)
        * **500** - Internal Server Error
        """,
        routes=app.routes,
    )
    
    # Add security scheme for JWT
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token obtained from /login endpoint"
        }
    }
    
    # Add security to all protected endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if openapi_schema["paths"][path][method].get("tags"):
                if any(tag in ["Users", "Categories", "Expenses"] 
                       for tag in openapi_schema["paths"][path][method]["tags"]):
                    openapi_schema["paths"][path][method]["security"] = [
                        {"HTTPBearer": []}
                    ]
    
    # Add examples to the schema
    openapi_schema["components"]["examples"] = {
        "UserRegistration": {
            "summary": "User Registration Example",
            "value": {
                "username": "johndoe",
                "email": "john.doe@example.com", 
                "password": "securepassword123"
            }
        },
        "ExpenseCreation": {
            "summary": "Expense Creation Example",
            "value": {
                "amount": 29.99,
                "description": "Lunch at restaurant",
                "date": "2024-01-15",
                "category_id": 1
            }
        },
        "CategoryCreation": {
            "summary": "Category Creation Example", 
            "value": {
                "name": "Food & Dining",
                "description": "Restaurant meals and food purchases"
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def setup_swagger_ui(app: FastAPI):
    """Setup custom Swagger UI configuration"""
    
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Interactive API Documentation",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_ui_parameters={
                "deepLinking": True,
                "displayRequestDuration": True,
                "docExpansion": "list",
                "operationsSorter": "method",
                "filter": True,
                "tagsSorter": "alpha",
                "tryItOutEnabled": True,
                "defaultModelsExpandDepth": 2,
                "defaultModelExpandDepth": 2,
                "displayOperationId": False,
                "showExtensions": True,
                "showCommonExtensions": True,
            }
        )
    
    return app

# Custom CSS for Swagger UI
CUSTOM_SWAGGER_CSS = """
<style>
.swagger-ui .topbar { 
    background-color: #2c3e50; 
}
.swagger-ui .info .title {
    color: #2c3e50;
    font-size: 2.5em;
}
.swagger-ui .scheme-container {
    background: #ecf0f1;
    border-radius: 4px;
    padding: 10px;
}
.swagger-ui .btn.authorize {
    background-color: #27ae60;
    border-color: #27ae60;
}
.swagger-ui .btn.authorize:hover {
    background-color: #2ecc71;
    border-color: #2ecc71;
}
</style>
"""