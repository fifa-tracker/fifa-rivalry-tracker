from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# Connect to MongoDB
client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]

async def get_database():
    """Get database dependency for dependency injection"""
    return db
