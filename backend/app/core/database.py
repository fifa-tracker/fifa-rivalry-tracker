from motor.motor_asyncio import AsyncIOMotorClient
from ..config.settings import MONGO_URI

# Create MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client.fifa_rivalry

# Get collections
players_collection = db.players
matches_collection = db.matches
tournaments_collection = db.tournaments 