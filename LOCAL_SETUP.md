# Local Development Setup

This Docker Compose configuration is designed for local development and uses:

- **MongoDB**: Local MongoDB container (version 7.0)
- **Backend**: Your FastAPI application
- **No Metabase**: Metabase is excluded for simpler local development

## Usage

1. Make sure you have a `.env` file with the required environment variables
2. Run the local development environment:

```bash
docker-compose -f docker-compose.local.yml up --build
```

3. The services will be available at:
   - Backend API: http://localhost:3000
   - MongoDB: localhost:27017

## Environment Variables

Make sure your `.env` file includes:
- `SECRET_KEY`: Your JWT secret key
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 43200)
- `LOG_LEVEL`: Logging level (default: INFO)

The MongoDB connection string is automatically set to `mongodb://mongodb:27017/fifa_rivalry` for local development.

## Database Initialization

The MongoDB container will automatically:
- Create the `fifa_rivalry` database
- Create necessary collections (users, matches, tournaments, players)
- Set up indexes for better performance

## Stopping the Services

```bash
docker-compose -f docker-compose.local.yml down
```

To also remove the MongoDB data volume:
```bash
docker-compose -f docker-compose.local.yml down -v
```
