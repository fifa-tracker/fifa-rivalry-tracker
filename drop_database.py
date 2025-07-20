#!/usr/bin/env python3
"""
Script to drop all collections in the FIFA Rivalry Tracker database.

WARNING: This will permanently delete all data including:
- Users/Players
- Matches
- Tournaments
- All statistics

Use with extreme caution!
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import pathlib
from dotenv import dotenv_values

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from .env file"""
    env_path = pathlib.Path(__file__).parent / '.env'
    config = dotenv_values(env_path)
    
    # Determine environment from .env file
    environment = config.get("ENVIRONMENT", "development")
    
    # Get MongoDB URI from .env file or use default based on environment
    mongo_uri = config.get("MONGO_URI") or config.get(f"MONGO_URI_{environment.upper()}")
    
    if not mongo_uri:
        raise ValueError("MongoDB URI not found in .env file")
    
    return mongo_uri

async def drop_all_collections():
    """Drop all collections in the fifa_rivalry database"""
    try:
        # Load configuration
        mongo_uri = load_config()
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_uri)
        
        # Test connection
        await client.admin.command('ping')
        logger.info("✅ MongoDB connection successful!")
        
        # Get database
        db = client.fifa_rivalry
        
        # List all collections before dropping
        collections = await db.list_collection_names()
        logger.info(f"📋 Collections found: {collections}")
        
        if not collections:
            logger.warning("⚠️  Database appears to be empty already")
            return
        
        # Confirm with user
        print("\n" + "="*60)
        print("🚨 WARNING: This will permanently delete ALL data! 🚨")
        print("="*60)
        print(f"Database: fifa_rivalry")
        print(f"Collections to drop: {', '.join(collections)}")
        print("="*60)
        
        confirmation = input("\nType 'DROP' to confirm collection deletion: ")
        
        if confirmation != "DROP":
            logger.info("❌ Collection deletion cancelled by user")
            return
        
        # Drop each collection individually
        logger.info("🗑️  Dropping collections...")
        dropped_collections = []
        
        for collection_name in collections:
            try:
                await db.drop_collection(collection_name)
                logger.info(f"✅ Dropped collection: {collection_name}")
                dropped_collections.append(collection_name)
            except Exception as e:
                logger.error(f"❌ Failed to drop collection {collection_name}: {str(e)}")
        
        # Verify all collections are gone
        remaining_collections = await db.list_collection_names()
        
        if not remaining_collections:
            logger.info("✅ All collections have been successfully dropped!")
            logger.info(f"📊 Summary: Dropped {len(dropped_collections)} collections")
        else:
            logger.warning(f"⚠️  Some collections remain: {remaining_collections}")
            
    except Exception as e:
        logger.error(f"❌ Error dropping collections: {str(e)}")
        raise
    finally:
        # Close the connection
        client.close()
        logger.info("🔌 Database connection closed")

def main():
    """Main function"""
    print("🗑️  FIFA Rivalry Tracker Collection Dropper")
    print("="*50)
    
    try:
        asyncio.run(drop_all_collections())
    except KeyboardInterrupt:
        logger.info("\n❌ Operation cancelled by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 