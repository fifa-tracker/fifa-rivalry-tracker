# JWT Authentication System

This document describes the JWT authentication system implemented in the FIFA Rivalry Tracker API.

## Overview

The API now uses JWT (JSON Web Tokens) for authentication. All API endpoints (except the root endpoint and authentication endpoints) require a valid JWT token in the Authorization header.

## Features

- **JWT Token Authentication**: Secure token-based authentication
- **Password Hashing**: Passwords are hashed using bcrypt
- **User Registration**: New users can register with username, email, and password
- **User Login**: Multiple login methods (form data and JSON)
- **Token Refresh**: Users can refresh their access tokens
- **User Roles**: Support for regular users and superusers
- **CORS Support**: Cross-origin requests are supported

## Setup

### 1. Install Dependencies

The following dependencies have been added to `requirements.txt`:

```txt
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
```

### 2. Create Default Users

Run the user creation script to set up default users:

Using `uv` (recommended):
```bash
uv run python create_admin_user.py
```

Or using `pip`:
```bash
python create_admin_user.py
```

This will create:
- **Admin User**: `admin` / `admin123` (superuser)
- **Test User**: `testuser` / `test123` (regular user)

⚠️ **Important**: Change these passwords in production!

### 3. Environment Variables

Add the following to your `.env` file:

```env
# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## API Endpoints

### Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "full_name": "New User",
  "password": "securepassword"
}
```

#### Login (Form Data)
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=newuser&password=securepassword
```

#### Login (JSON)
```http
POST /api/v1/auth/login-json
Content-Type: application/json

{
  "username": "newuser",
  "password": "securepassword"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <your-jwt-token>
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <your-jwt-token>
```

### Protected Endpoints

All other endpoints now require authentication. Include the JWT token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

## Usage Examples

### 1. Register a New User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "password": "mypassword123"
  }'
```

### 2. Login and Get Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "mypassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Use Token to Access Protected Endpoints

```bash
curl -X GET "http://localhost:8000/api/v1/players" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## Security Considerations

### 1. Secret Key
- Change the `SECRET_KEY` in production
- Use a strong, random secret key
- Keep the secret key secure and never commit it to version control

### 2. Token Expiration
- Tokens expire after 30 minutes by default
- Users should refresh tokens before expiration
- Consider implementing refresh tokens for better security

### 3. Password Security
- Passwords are hashed using bcrypt
- Minimum password requirements should be enforced
- Consider implementing password reset functionality

### 4. CORS Configuration
- Configure CORS properly for production
- Restrict allowed origins to your frontend domain
- Don't use `allow_origins=["*"]` in production

## Database Schema

### Users Collection

```javascript
{
  "_id": ObjectId,
  "username": "string",
  "email": "string",
  "full_name": "string",
  "hashed_password": "string",
  "is_active": boolean,
  "is_superuser": boolean,
  "created_at": datetime,
  "updated_at": datetime
}
```

## Error Handling

### Authentication Errors

- **401 Unauthorized**: Invalid or missing token
- **400 Bad Request**: Inactive user
- **403 Forbidden**: Insufficient permissions (for superuser endpoints)

### Common Error Responses

```json
{
  "detail": "Could not validate credentials"
}
```

```json
{
  "detail": "Incorrect username or password"
}
```

## Testing

### 1. Test Authentication Flow

1. Register a new user
2. Login to get a token
3. Use the token to access protected endpoints
4. Test token refresh

### 2. Test Error Cases

1. Try to access protected endpoints without a token
2. Use an invalid token
3. Use an expired token
4. Try to login with wrong credentials

## Production Deployment

### 1. Environment Variables

Set these environment variables in production:

```env
SECRET_KEY=your-production-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
MONGO_URI=your-production-mongodb-uri
```

### 2. Security Headers

Add security headers to your deployment:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])
```

### 3. Rate Limiting

Consider implementing rate limiting for authentication endpoints:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

## Troubleshooting

### Common Issues

1. **"Could not validate credentials"**
   - Check if the token is valid and not expired
   - Verify the token format in the Authorization header

2. **"User not found"**
   - The user might have been deleted
   - Check if the username in the token matches a user in the database

3. **"Inactive user"**
   - The user account has been deactivated
   - Contact an administrator to reactivate the account

4. **Database Connection Issues**
   - Verify MongoDB connection string
   - Check if the users collection exists

### Debug Mode

Enable debug logging by setting the log level:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **Refresh Tokens**: Implement refresh token rotation
2. **Password Reset**: Add password reset functionality
3. **Email Verification**: Require email verification for new accounts
4. **OAuth Integration**: Add social login options
5. **Role-Based Access Control**: Implement more granular permissions
6. **Audit Logging**: Log authentication events for security monitoring 