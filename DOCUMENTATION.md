# FIFA Rivalry Tracker - Complete Documentation

A comprehensive guide to the FIFA Rivalry Tracker application, including setup, configuration, deployment, and feature documentation.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Quick Start Guide](#quick-start-guide)
3. [Configuration](#configuration)
4. [Authentication System](#authentication-system)
5. [Google OAuth Integration](#google-oauth-integration)
6. [ELO Rating System](#elo-rating-system)
7. [Features](#features)
8. [API Documentation](#api-documentation)
9. [Deployment](#deployment)
10. [Database Migrations](#database-migrations)
11. [Development](#development)
12. [Testing](#testing)
13. [Troubleshooting](#troubleshooting)

---

## Project Overview

A FastAPI-based backend application for tracking FIFA match results and player statistics with JWT authentication.

### Features

- **JWT Authentication**: Secure token-based authentication for all API endpoints
- **Player Management**: Register, view, update, and delete players
- **Match Tracking**: Record and manage match results
- **Tournament Support**: Create and manage tournaments
- **Statistics**: Comprehensive player and tournament statistics
- **MongoDB Integration**: NoSQL database for flexible data storage
- **Docker Support**: Easy deployment with Docker containers
- **ELO Rating System**: Dynamic player ranking system
- **Google OAuth**: Social login integration
- **Last Teams Tracking**: Track recent unique teams played

### Prerequisites

- Python 3.12+
- MongoDB (local or MongoDB Atlas)
- Docker (optional)
- uv (recommended) or pip

---

## Quick Start Guide

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fifa-rivalry-tracker
```

### 2. Install Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or using `pip`:
```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the root directory:

```env
# Environment
ENVIRONMENT=development

# Database
MONGO_URI=your-mongodb-connection-string

# JWT Authentication
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Logging (optional)
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 4. Create Default Users

Run the user creation script to set up default users:

```bash
# Using uv
uv run python create_admin_user.py

# Or using pip
python create_admin_user.py
```

This creates:
- **Admin User**: `admin` / `admin123` (superuser)
- **Test User**: `testuser` / `test123` (regular user)

⚠️ **Important**: Change these passwords in production!

### 5. Start the Server

Using `uv`:
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or using `pip`:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 6. API Documentation

- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

#### Required Configuration

```env
# Environment
ENVIRONMENT=development

# Database
MONGO_URI=mongodb://localhost:27017/fifa_rivalry
# Or for MongoDB Atlas:
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/fifa_rivalry?retryWrites=true&w=majority

# JWT Authentication
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

#### Logging Configuration

```env
# Logging Configuration
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Optional: Custom log format
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Optional: Log to file (creates logs directory automatically)
LOG_FILE=logs/app.log
```

#### Google OAuth Configuration

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical errors that may prevent the application from running

### Configuration Validation

The application validates configuration on startup and will raise errors for:
- Missing required environment variables
- Invalid log levels
- Production environment with default secret key

---

## Authentication System

### Overview

The API uses JWT (JSON Web Tokens) for authentication. All API endpoints (except the root endpoint and authentication endpoints) require a valid JWT token in the Authorization header.

### Features

- **JWT Token Authentication**: Secure token-based authentication
- **Password Hashing**: Passwords are hashed using bcrypt
- **User Registration**: New users can register with username, email, and password
- **User Login**: Multiple login methods (form data and JSON)
- **Token Refresh**: Users can refresh their access tokens
- **User Roles**: Support for regular users and superusers
- **CORS Support**: Cross-origin requests are supported

### API Endpoints

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "first_name": "New",
  "last_name": "User",
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

### Usage Examples

#### 1. Register a New User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "mypassword123"
  }'
```

#### 2. Login and Get Token

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

#### 3. Use Token to Access Protected Endpoints

```bash
curl -X GET "http://localhost:8000/api/v1/players" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Security Considerations

1. **Secret Key**: Change the `SECRET_KEY` in production
2. **Token Expiration**: Tokens expire after 1 month (43,200 minutes) by default
3. **Password Security**: Passwords are hashed using bcrypt
4. **CORS Configuration**: Configure CORS properly for production

---

## Google OAuth Integration

### Overview

The Google OAuth integration allows users to authenticate using their Google accounts instead of creating separate credentials.

### Setup Instructions

#### 1. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Create OAuth 2.0 credentials:
   - Choose "Web application" as the application type
   - Add authorized redirect URIs:
     - For development: `http://localhost:8000/api/v1/auth/google/callback`
     - For production: `https://yourdomain.com/api/v1/auth/google/callback`

#### 2. Environment Configuration

Add the following variables to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

### API Endpoints

#### 1. Initiate Google Login

**GET** `/api/v1/auth/google/login`

Returns the Google OAuth authorization URL.

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=..."
}
```

#### 2. Handle OAuth Callback

**GET** `/api/v1/auth/google/callback`

Handles the OAuth callback with authorization code.

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

#### 3. Verify ID Token

**POST** `/api/v1/auth/google/verify`

Alternative endpoint for verifying Google ID tokens directly.

**Request Body:**
```json
{
  "id_token": "google_id_token"
}
```

### Frontend Integration

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

---

## ELO Rating System

### Overview

The ELO rating system has been integrated into the match recording functionality to provide a fair and dynamic ranking system for players. ELO ratings are automatically calculated and updated whenever matches are recorded, updated, or deleted.

### Implementation Details

#### ELO Calculation Module

The core ELO calculation logic is implemented in the `app/utils/elo.py` module with two main functions:
- `calculate_elo_ratings(player1_rating, player2_rating, player1_goals, player2_goals)`: Calculates new ELO ratings for both players after a match
- `calculate_elo_change(player1_rating, player2_rating, player1_goals, player2_goals)`: Calculates the ELO rating changes for both players

#### Configuration

ELO settings are configurable through the application settings:

```python
# ELO Rating
DEFAULT_ELO_RATING: int = 1200  # Starting ELO rating for new players
ELO_K_FACTOR: int = 32          # K-factor determines rating change magnitude
```

### ELO Formula

The implementation uses the standard ELO rating formula:

1. **Expected Score Calculation**:
   ```
   Expected Score = 1 / (1 + 10^((opponent_rating - player_rating) / 400))
   ```

2. **Actual Score Assignment**:
   - Win: 1.0
   - Draw: 0.5
   - Loss: 0.0

3. **New Rating Calculation**:
   ```
   New Rating = Current Rating + K * (Actual Score - Expected Score)
   ```

4. **K-Factor**: Currently set to 32, which provides moderate rating volatility

### Key Features

- **Zero-Sum Property**: The total rating points in the system remain constant
- **Upset Bonuses**: Lower-rated players who defeat higher-rated opponents gain more rating points
- **Expected Win Penalties**: Higher-rated players who defeat lower-rated opponents gain fewer points
- **Draw Handling**: When players draw, both players experience minimal rating changes

### Example Calculations

#### Equal Ratings (1200 vs 1200)
- **Player 1 wins 3-1**: Player 1 gains +16, Player 2 loses -16
- **Player 2 wins 1-3**: Player 1 loses -16, Player 2 gains +16
- **Draw 2-2**: Both players experience 0 change

#### Upset Win (1000 vs 1400)
- **Lower-rated player wins 3-1**: Player 1 gains +29, Player 2 loses -29

#### Expected Win (1400 vs 1000)
- **Higher-rated player wins 3-1**: Player 1 gains +3, Player 2 loses -3

---

## Features

### Last 5 Teams Feature

Each user has a `last_5_teams` field that tracks the last 5 **unique** teams they have played with in matches.

#### Field Details

- **Field Name**: `last_5_teams`
- **Type**: `List[str]`
- **Default Value**: `[]` (empty list)
- **Maximum Length**: 5 unique teams
- **Update Behavior**: 
  - If the team already exists in the list, it's moved to the front (most recent position)
  - If it's a new team, it's added to the front
  - Only unique teams are kept (no duplicates)
  - Oldest teams are removed when the list exceeds 5 unique teams

#### API Response

The `last_5_teams` field is included in all user/player API responses:

```json
{
  "id": "user_id",
  "username": "player1",
  "last_5_teams": ["Barcelona", "Real Madrid", "Arsenal", "Chelsea", "Liverpool"],
  ...
}
```

---

## API Documentation

### Authentication (Public)
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login with form data
- `POST /api/v1/auth/login-json` - Login with JSON
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/refresh` - Refresh access token

### Players (Protected)
- `GET /api/v1/players` - Get all players
- `POST /api/v1/players` - Register new player
- `GET /api/v1/players/{id}` - Get specific player
- `PUT /api/v1/players/{id}` - Update player
- `DELETE /api/v1/players/{id}` - Delete player
- `GET /api/v1/players/{id}/stats` - Get player statistics
- `GET /api/v1/players/{id}/matches` - Get player matches

### Matches (Protected)
- `GET /api/v1/matches` - Get all matches
- `POST /api/v1/matches` - Record new match
- `PUT /api/v1/matches/{id}` - Update match
- `DELETE /api/v1/matches/{id}` - Delete match

### Tournaments (Protected)
- `GET /api/v1/tournaments` - Get all tournaments
- `POST /api/v1/tournaments` - Create new tournament
- `GET /api/v1/tournaments/{id}` - Get specific tournament
- `GET /api/v1/tournaments/{id}/matches` - Get tournament matches
- `GET /api/v1/tournaments/{id}/stats` - Get tournament statistics
- `POST /api/v1/tournaments/{id}/players` - Add player to tournament
- `DELETE /api/v1/tournaments/{id}/players/{player_id}` - Remove player from tournament

### Statistics (Protected)
- `GET /api/v1/stats` - Get player leaderboard

### Authentication

All protected endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

---

## Deployment

### Docker Deployment

#### On RPI (Raspberry Pi)
```bash
sudo docker compose -f ./docker-compose-rpi.yaml up -d
```

#### On x86 or Apple Silicon
```bash
sudo docker compose -f ./docker-compose-standard.yaml up -d
```

#### Production
```bash
sudo docker compose -f ./docker-compose.yml up -d
```

### GitHub Actions Deployment

This project includes a GitHub Actions workflow for automated deployment to your production server.

#### Prerequisites

1. **SSH Access**: Ensure you have SSH access to your production server
2. **Docker & Docker Compose**: Make sure Docker and Docker Compose are installed on your server
3. **GitHub Repository**: Your code should be in a GitHub repository

#### GitHub Secrets Setup

You need to configure the following secrets in your GitHub repository:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following repository secrets:

##### Required Secrets

- `SSH_USERNAME`: The username for SSH access to your server
- `SSH_PRIVATE_KEY`: Your private SSH key (the entire key content)
- `SSH_PORT`: The SSH port (usually 22)
- `MONGO_URI`: Your MongoDB connection string
- `SECRET_KEY`: A secure secret key for JWT authentication

#### How the Deployment Works

The workflow will:
1. **Trigger**: Run on pushes to `main` or `master` branch, or manually via workflow dispatch
2. **SSH Connection**: Connect to your server using the provided credentials
3. **Code Update**: Clone the repository (if first time) or pull latest changes
4. **Docker Deployment**: Stop existing containers, build new images, and start the application
5. **Health Check**: Verify the application is running on port 3000
6. **Cleanup**: Remove old Docker images to save space

### Nginx Configuration

The nginx configuration provides:
1. **HTTP Server (Port 80)**: Serves content directly without redirects
2. **HTTPS Server (Port 443)**: Optional SSL configuration for secure connections
3. **Proxy Configuration**: Routes traffic to the Docker container running on port 3000
4. **WebSocket Support**: Enables real-time communication
5. **Static File Caching**: Optimizes performance for static assets
6. **Health Check Endpoint**: Dedicated endpoint for monitoring
7. **API Routing**: Proper handling of API requests

#### Setup Instructions

Run the setup script on your VM:

```bash
sudo ./scripts/setup_nginx.sh
```

---

## Database Migrations

### Name Field Migration

The application has been updated to split the user's name field into two separate fields:
- `first_name`: The user's first name
- `last_name`: The user's last name (including middle names, prefixes, etc.)

#### Migration Script

Run the migration script:

```bash
python scripts/migrate_name_fields.py
```

This script will:
1. Find all users with a `name` field
2. Split the name into `first_name` and `last_name`
3. Update the database records
4. Remove the old `name` field

#### Name Splitting Logic

The script handles various name formats:
- `"John Doe"` → `first_name: "John"`, `last_name: "Doe"`
- `"John"` → `first_name: "John"`, `last_name: ""`
- `"John van Doe"` → `first_name: "John"`, `last_name: "van Doe"`
- `"John van der Doe"` → `first_name: "John"`, `last_name: "van der Doe"`

### Last Teams Migration

For existing users, run the migration script:

```bash
python scripts/migrate_last_teams.py
```

This script will:
- Add the `last_5_teams` field to all existing users
- Populate the field with unique teams from their recent matches (up to 5 unique teams)
- Update the `updated_at` timestamp

---

## Development

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# Run the application
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run pytest

# Run user creation script
uv run python create_admin_user.py

# Add new dependencies
uv add package-name

# Add development dependencies
uv add --dev package-name
```

### Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run user creation script
python create_admin_user.py
```

### Project Structure

```
fifa-rivalry-tracker/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py          # Authentication endpoints
│   │   │   │   ├── players.py       # Player management
│   │   │   │   ├── matches.py       # Match management
│   │   │   │   ├── tournaments.py   # Tournament management
│   │   │   │   └── stats.py         # Statistics
│   │   │   └── router.py            # API router
│   │   └── dependencies.py          # Database dependencies
│   ├── models/
│   │   ├── auth.py                  # Authentication models
│   │   ├── player.py                # Player models
│   │   ├── match.py                 # Match models
│   │   └── tournament.py            # Tournament models
│   ├── utils/
│   │   ├── auth.py                  # Authentication utilities
│   │   ├── elo.py                   # ELO rating calculations
│   │   ├── google_oauth.py          # Google OAuth utilities
│   │   └── helpers.py               # Helper functions
│   └── config.py                    # Application configuration
├── scripts/                         # Utility scripts
├── tests/                          # Test files
├── nginx/                          # Nginx configuration
└── docker-compose*.yaml            # Docker configurations
```

---

## Testing

Run the test suite:

Using `uv`:
```bash
uv run pytest
```

Or using `pip`:
```bash
pytest
```

### Test Coverage

The implementation includes comprehensive tests that verify:
- Basic win/loss scenarios
- Draw scenarios
- Upset wins (lower-rated player wins)
- Expected wins (higher-rated player wins)
- Zero-sum property maintenance
- K-factor impact on rating changes
- Authentication flows
- API endpoint functionality

---

## Troubleshooting

### Common Issues

#### Authentication Issues

1. **"Could not validate credentials"**
   - Check if the token is valid and not expired
   - Verify the token format in the Authorization header

2. **"User not found"**
   - The user might have been deleted
   - Check if the username in the token matches a user in the database

3. **"Inactive user"**
   - The user account has been deactivated
   - Contact an administrator to reactivate the account

#### Database Issues

1. **Database Connection Issues**
   - Verify MongoDB connection string
   - Check if the users collection exists

2. **Migration Issues**
   - Make sure you're running the script from the project root directory
   - Verify your MongoDB connection string in the environment variables

#### Deployment Issues

1. **SSH Connection Failed**: 
   - Verify your SSH credentials are correct
   - Ensure the server is accessible from GitHub Actions
   - Check if the SSH port is correct

2. **Docker Build Failed**:
   - Check the Dockerfile and docker-compose.yml files
   - Ensure all required files are present in the repository

3. **Application Not Starting**:
   - Check the application logs: `docker-compose logs`
   - Verify environment variables are set correctly
   - Ensure the MongoDB connection is working

### Debug Commands

```bash
# Test environment variables locally
python3 scripts/test_env.py

# Generate a new secret key
python3 scripts/generate_secret_key.py

# Test the migration
python3 scripts/test_migration.py

# Check if .env file exists and has content
ls -la .env
cat .env | sed 's/=.*/=***/'
```

### Debug Mode

Enable debug logging by setting the log level:

```bash
# Debug logging to console
LOG_LEVEL=DEBUG uvicorn main:app --reload

# Info logging to file
LOG_LEVEL=INFO LOG_FILE=logs/app.log uvicorn main:app --reload
```

---

## Security Considerations

- Change the default `SECRET_KEY` in production
- Use strong passwords for admin accounts
- Configure CORS properly for your frontend domain
- Implement rate limiting for production deployments
- Use HTTPS in production
- Keep your SSH private key secure and never commit it to version control
- Use a dedicated deployment user on your server with limited permissions
- Consider using SSH key rotation for better security
- Monitor your server logs regularly for any security issues

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

---

## License

This project is licensed under the MIT License.
