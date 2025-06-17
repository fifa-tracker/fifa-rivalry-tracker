from motor.motor_asyncio import AsyncIOMotorClient
import pathlib
from dotenv import dotenv_values

# Load environment variables
env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
config = dotenv_values(env_path)

# Determine environment from .env file
ENVIRONMENT = config.get("ENVIRONMENT", "development")

# Get MongoDB URI from .env file or use default based on environment
mongo_uri = config.get("MONGO_URI") or config.get(f"MONGO_URI_{ENVIRONMENT.upper()}")

# Connect to MongoDB
client = AsyncIOMotorClient(mongo_uri)
db = client.fifa_rivalry

async def get_database():
    """Get database dependency for dependency injection"""
    return db
