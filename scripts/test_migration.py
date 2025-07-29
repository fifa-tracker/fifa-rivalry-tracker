#!/usr/bin/env python3
"""
Test script to verify that the name field migration works correctly.
This script will:
1. Create a test user with a name field
2. Run the migration
3. Verify that the name field was split correctly
4. Clean up the test data
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.api.dependencies import get_database
from app.utils.auth import get_password_hash
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def create_test_user_with_name():
    """Create a test user with a name field to test migration"""
    db = await get_database()
    
    # Create test user data with name field
    test_user_data = {
        "username": "migration_test_user",
        "email": "migration@test.com",
        "name": "John van der Doe",  # This should be split into first_name and last_name
        "hashed_password": get_password_hash("test123"),
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        # Initialize player statistics
        "total_matches": 0,
        "total_goals_scored": 0,
        "total_goals_conceded": 0,
        "goal_difference": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "points": 0,
        # ELO rating and tournament fields
        "elo_rating": 1200,
        "tournaments_played": 0,
        "tournament_ids": []
    }
    
    # Insert test user
    result = await db.users.insert_one(test_user_data)
    
    if result.inserted_id:
        logger.info("✅ Test user created successfully!")
        logger.info(f"Username: {test_user_data['username']}")
        logger.info(f"Name: {test_user_data['name']}")
        return str(result.inserted_id)
    else:
        logger.error("❌ Failed to create test user")
        return None


async def verify_migration_results():
    """Verify that the migration worked correctly"""
    db = await get_database()
    
    # Find the test user
    user = await db.users.find_one({"username": "migration_test_user"})
    
    if not user:
        logger.error("❌ Test user not found after migration")
        return False
    
    # Check that the old name field is gone
    if "name" in user:
        logger.error("❌ Old 'name' field still exists")
        return False
    
    # Check that new fields exist
    if "first_name" not in user or "last_name" not in user:
        logger.error("❌ New 'first_name' or 'last_name' fields missing")
        return False
    
    # Check the values
    expected_first_name = "John"
    expected_last_name = "van der Doe"
    
    if user["first_name"] != expected_first_name:
        logger.error(f"❌ Expected first_name '{expected_first_name}', got '{user['first_name']}'")
        return False
    
    if user["last_name"] != expected_last_name:
        logger.error(f"❌ Expected last_name '{expected_last_name}', got '{user['last_name']}'")
        return False
    
    logger.info("✅ Migration verification successful!")
    logger.info(f"First name: {user['first_name']}")
    logger.info(f"Last name: {user['last_name']}")
    return True


async def cleanup_test_data():
    """Clean up the test user"""
    db = await get_database()
    
    result = await db.users.delete_one({"username": "migration_test_user"})
    
    if result.deleted_count > 0:
        logger.info("✅ Test user cleaned up successfully")
    else:
        logger.warning("⚠️  Test user not found for cleanup")


async def main():
    """Main test function"""
    try:
        logger.info("🧪 Starting migration test...")
        
        # Step 1: Create test user with name field
        logger.info("Step 1: Creating test user with name field...")
        user_id = await create_test_user_with_name()
        if not user_id:
            logger.error("❌ Failed to create test user")
            return
        
        # Step 2: Run the migration
        logger.info("Step 2: Running migration...")
        from scripts.migrate_name_fields import migrate_user_names
        await migrate_user_names()
        
        # Step 3: Verify results
        logger.info("Step 3: Verifying migration results...")
        success = await verify_migration_results()
        
        if success:
            logger.info("🎉 Migration test completed successfully!")
        else:
            logger.error("❌ Migration test failed!")
            return
        
        # Step 4: Cleanup
        logger.info("Step 4: Cleaning up test data...")
        await cleanup_test_data()
        
        logger.info("✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        # Try to cleanup even if test failed
        try:
            await cleanup_test_data()
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 