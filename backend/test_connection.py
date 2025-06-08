from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import dotenv_values
import pathlib

# Load environment variables
env_path = pathlib.Path(__file__).parent / '.env'
config = dotenv_values(env_path)

async def test_mongodb_connection():
    mongo_uri = config.get("MONGO_URI")
    print(f"Testing connection to: {mongo_uri}")
    
    try:
        client = AsyncIOMotorClient(mongo_uri)
        # Ping the database
        await client.admin.command('ping')
        print("✅ MongoDB Atlas connection successful!")
        
        # Test database access
        db = client.fifa_rivalry
        collections = await db.list_collection_names()
        print(f"📁 Available collections: {collections}")
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify IP is whitelisted in MongoDB Atlas")
        print("3. Check username/password in connection string")
        print("4. Ensure database name is included in URI")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection()) 