# FIFA Rivalry Tracker

A FastAPI-based backend application for tracking FIFA match results and player statistics with JWT authentication.

## Features

- **JWT Authentication**: Secure token-based authentication for all API endpoints
- **Player Management**: Register, view, update, and delete players
- **Match Tracking**: Record and manage match results
- **Tournament Support**: Create and manage tournaments
- **Statistics**: Comprehensive player and tournament statistics
- **MongoDB Integration**: NoSQL database for flexible data storage
- **Docker Support**: Easy deployment with Docker containers

## Quick Start

### Prerequisites

- Python 3.12+
- MongoDB (local or MongoDB Atlas)
- Docker (optional)
- uv (recommended) or pip

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
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging (optional)
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

For detailed configuration options, see [CONFIGURATION.md](CONFIGURATION.md).

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

## API Documentation

- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Authentication Guide**: See [AUTHENTICATION.md](AUTHENTICATION.md)

## Docker Deployment

### On RPI (Raspberry Pi)
```bash
sudo docker compose -f ./docker-compose-rpi.yaml up -d
```

### On x86 or Apple Silicon
```bash
sudo docker compose -f ./docker-compose-standard.yaml up -d
```

### Production
```bash
sudo docker compose -f ./docker-compose.yml up -d
```

## API Endpoints

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

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Example Usage

1. **Register a user:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com", "password": "password123"}'
```

2. **Login to get token:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "password123"}'
```

3. **Use token to access protected endpoints:**
```bash
curl -X GET "http://localhost:8000/api/v1/players" \
  -H "Authorization: Bearer <your-token>"
```

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

## Logging

The application uses centralized logging configuration. You can control log levels and output through environment variables:

```bash
# Debug logging to console
LOG_LEVEL=DEBUG uvicorn main:app --reload

# Info logging to file
LOG_LEVEL=INFO LOG_FILE=logs/app.log uvicorn main:app --reload
```

For detailed logging configuration, see [CONFIGURATION.md](CONFIGURATION.md).

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

## Project Structure

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
│   │   └── helpers.py               # Helper functions
│   └── main.py                      # FastAPI application
├── create_admin_user.py             # User creation script
├── AUTHENTICATION.md                # Authentication documentation
├── pyproject.toml                   # Project configuration (uv)
├── uv.lock                          # Lock file (uv)
├── requirements.txt                 # Python dependencies (pip)
└── docker-compose*.yaml            # Docker configurations
```

## Security Considerations

- Change the default `SECRET_KEY` in production
- Use strong passwords for admin accounts
- Configure CORS properly for your frontend domain
- Implement rate limiting for production deployments
- Use HTTPS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.