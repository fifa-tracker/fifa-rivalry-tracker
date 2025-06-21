import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_database
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import asyncio
from typing import AsyncGenerator, Generator

# Load environment variables
load_dotenv()

# Test database name
TEST_DB_NAME = "fifa_rivalry_test"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    # Don't close the loop here as it might be reused

@pytest.fixture
def client() -> TestClient:
    """Test client fixture"""
    return TestClient(app)

@pytest.fixture
def sample_player_data():
    """Sample player data for testing"""
    return {
        "name": "Test Player"
    }

@pytest.fixture
def sample_match_data():
    """Sample match data for testing"""
    return {
        "player1_id": "507f1f77bcf86cd799439011",  # Example ObjectId
        "player2_id": "507f1f77bcf86cd799439012",  # Example ObjectId
        "player1_goals": 2,
        "player2_goals": 1,
        "team1": "Team A",
        "team2": "Team B"
    }

@pytest.fixture
def sample_tournament_data():
    """Sample tournament data for testing"""
    return {
        "name": "Test Tournament",
        "start_date": "2024-03-20",
        "end_date": "2024-03-25",
        "description": "A test tournament for testing purposes",
        "player_ids": []
    }

@pytest_asyncio.fixture
async def created_players(client, sample_player_data):
    """Create test players and return them"""
    players = []
    for i in range(2):
        player_data = {**sample_player_data, "name": f"Test Player {i+1}"}
        response = client.post("/api/v1/players/", json=player_data)
        assert response.status_code == 200
        players.append(response.json())
    return players

@pytest_asyncio.fixture
async def created_tournament(client, sample_tournament_data):
    """Create a test tournament and return it"""
    response = client.post("/api/v1/tournaments/", json=sample_tournament_data)
    assert response.status_code == 200
    return response.json()

@pytest_asyncio.fixture(autouse=True)
async def setup_test_database() -> AsyncGenerator:
    """Setup and teardown test database"""
    # Get MongoDB URI from environment
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable not set")

    # Create test client
    client = AsyncIOMotorClient(mongo_uri)
    db = client[TEST_DB_NAME]

    # Clear all collections before each test
    await db.players.delete_many({})
    await db.matches.delete_many({})
    await db.tournaments.delete_many({})

    # Override the database dependency
    app.dependency_overrides[get_database] = lambda: db

    yield db

    # Cleanup after tests - just clear collections instead of dropping database
    await db.players.delete_many({})
    await db.matches.delete_many({})
    await db.tournaments.delete_many({})
    client.close() 