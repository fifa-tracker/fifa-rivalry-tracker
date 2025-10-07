# Google OAuth Integration Guide

This guide explains how to set up and use Google OAuth authentication in the FIFA Rivalry Tracker API.

## Overview

The Google OAuth integration allows users to authenticate using their Google accounts instead of creating separate credentials. This provides a seamless login experience and reduces password management overhead.

## Setup Instructions

### 1. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Web application" as the application type
   - Add authorized redirect URIs:
     - For development: `http://localhost:8000/api/v1/auth/google/callback`
     - For production: `https://yourdomain.com/api/v1/auth/google/callback`

### 2. Environment Configuration

Add the following variables to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

### 3. Install Dependencies

The required dependencies are already added to `pyproject.toml`:

```toml
dependencies = [
    "google-auth>=2.23.0",
    "google-auth-oauthlib>=1.1.0",
    "google-auth-httplib2>=0.1.1",
    "httpx>=0.25.0",
]
```

Install them with:
```bash
uv sync
```

## API Endpoints

### 1. Initiate Google Login

**GET** `/api/v1/auth/google/login`

Returns the Google OAuth authorization URL.

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=..."
}
```

### 2. Handle OAuth Callback

**GET** `/api/v1/auth/google/callback`

Handles the OAuth callback with authorization code. Google redirects here automatically after user authorization.

**Query Parameters:**
- `code`: Authorization code from Google
- `state`: Optional state parameter

**URL Example:**
```
http://localhost:8000/api/v1/auth/google/callback?code=4/0AVGzR1BgkE7ANz845BzRXdxDuk3gOn_If10xsW21yGb8VwPyh2lfIxdOUsFmP7u8bVfDGg&scope=email+profile+openid
```

**Alternative POST endpoint** `/api/v1/auth/google/callback` (POST) is also available for programmatic access:

**Request Body:**
```json
{
  "code": "authorization_code_from_google",
  "state": "optional_state_parameter"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "expires_in": 2592000,
  "email": "user@example.com",
  "username": "user"
}
```

### 3. Verify ID Token

**POST** `/api/v1/auth/google/verify`

Alternative endpoint for verifying Google ID tokens directly.

**Request Body:**
```json
{
  "id_token": "google_id_token"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "expires_in": 2592000,
  "email": "user@example.com",
  "username": "user"
}
```

## User Management

### OAuth User Creation

When a user authenticates via Google OAuth for the first time:

1. The system extracts user information from Google (email, name, profile picture)
2. A username is generated from the email address (e.g., `john.doe` from `john.doe@gmail.com`)
3. If the username already exists, a number is appended (e.g., `john.doe1`)
4. The user is created with `oauth_provider: "google"` and `oauth_id` set to the Google user ID

### Account Linking

If a user with the same email address already exists (created via regular registration):

1. The existing account is linked to Google OAuth
2. The `oauth_provider` is updated to `"google"`
3. The `oauth_id` is set to the Google user ID
4. The user can now log in using either method

### User Model Updates

The user model now includes OAuth-related fields:

```python
class User(UserBase):
    # ... existing fields ...
    oauth_provider: Optional[OAuthProvider] = OAuthProvider.LOCAL
    oauth_id: Optional[str] = None  # Google ID, etc.
```

## Frontend Integration

### Option 1: Authorization Code Flow

1. Redirect user to `/api/v1/auth/google/login` to get the auth URL
2. Redirect user to the Google auth URL
3. Handle the callback with the authorization code
4. Send the code to `/api/v1/auth/google/callback`

### Option 2: ID Token Verification

1. Use Google's JavaScript SDK to get an ID token
2. Send the ID token to `/api/v1/auth/google/verify`

Example JavaScript integration:

```javascript
// Using Google Sign-In JavaScript SDK
function onGoogleSignIn(googleUser) {
    const idToken = googleUser.getAuthResponse().id_token;
    
    fetch('/api/v1/auth/google/verify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            id_token: idToken
        })
    })
    .then(response => response.json())
    .then(data => {
        // Store the access token
        localStorage.setItem('access_token', data.access_token);
        // Redirect to dashboard or update UI
    });
}
```

## Security Considerations

1. **Token Validation**: All Google tokens are validated against Google's servers
2. **Email Verification**: The system checks if the Google account email is verified
3. **Account Linking**: Existing accounts are safely linked to Google OAuth
4. **JWT Tokens**: Standard JWT tokens are issued for API access
5. **HTTPS**: Always use HTTPS in production for OAuth redirects

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid request data or Google token
- `401 Unauthorized`: Invalid or expired Google token
- `500 Internal Server Error`: Server-side errors during OAuth processing

## Testing

You can test the Google OAuth integration using:

1. **Postman/Insomnia**: Test the endpoints directly
2. **Frontend Integration**: Implement the JavaScript SDK
3. **Unit Tests**: Test the utility functions with mock data

## Troubleshooting

### Common Issues

1. **Invalid Client ID**: Ensure `GOOGLE_CLIENT_ID` is correctly set
2. **Redirect URI Mismatch**: Check that the redirect URI in Google Console matches your configuration
3. **Token Expiration**: Google tokens expire quickly; implement proper refresh logic
4. **CORS Issues**: Ensure your frontend domain is in the CORS origins list

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your environment variables to see detailed OAuth flow information.

## Migration Notes

Existing users can continue to use their regular username/password authentication. The OAuth integration is additive and doesn't break existing functionality.

Users who want to link their existing accounts to Google OAuth can do so by logging in with Google using the same email address they used for registration.
