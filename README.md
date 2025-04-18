# FIFA Rivalry Tracker

A web application for tracking FIFA matches and player statistics.

## Features

- Track matches between players
- Record goals scored and conceded
- Calculate player statistics and rankings
- Head-to-head match history
- Tournament support
- Detailed player statistics

## Project Structure

```
fifa-rivalry-tracker/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── player.py
│   │   │   ├── match.py
│   │   │   └── tournament.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── player.py
│   │   │   ├── match.py
│   │   │   └── tournament.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── players.py
│   │   │   ├── matches.py
│   │   │   └── tournaments.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── database.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_players.py
│   │   ├── test_matches.py
│   │   └── test_tournaments.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── services/
    │   └── utils/
    ├── public/
    └── package.json
```

## Setup

1. Clone the repository
2. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the backend directory with the following variables:
   ```
   ENVIRONMENT=development
   MONGO_URI=mongodb://localhost:27017/fifa_rivalry
   ```
4. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT

# On RPI
sudo docker compose -f ./docker-compose-rpi.yaml up -d

# On x86 or Apple Silicon
sudo docker compose -f ./docker-compose-standard.yaml up -d