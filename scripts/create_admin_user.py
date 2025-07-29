#!/usr/bin/env python3
"""
Script to create a default admin user for testing purposes.
Run this script once to set up an initial admin user.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.api.dependencies import get_database
from app.utils.auth import get_password_hash
from app.utils.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)


async def create_admin_user():
    """Create a default admin user"""
    db = await get_database()
    
    # Check if admin user already exists
    existing_admin = await db.users.find_one({"username": "admin"})
    if existing_admin:
        logger.info("✅ Admin user already exists!")
        return
    
    # Create admin user data
    admin_data = {
        "username": "admin",
        "email": "admin@fifa-tracker.com",
        "first_name": "Administrator",
        "last_name": "",
        "hashed_password": get_password_hash("admin123"),  # Change this password!
        "is_active": True,
        "is_superuser": True,
        "created_at": datetime.now(datetime.UTC),
        "updated_at": datetime.now(datetime.UTC),
        # Initialize player statistics
        "total_matches": 0,
        "total_goals_scored": 0,
        "total_goals_conceded": 0,
        "goal_difference": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "points": 0
    }
    
    # Insert admin user
    result = await db.users.insert_one(admin_data)
    
    if result.inserted_id:
        logger.info("✅ Admin user created successfully!")
        logger.info("Username: admin")
        logger.info("Password: admin123")
        logger.warning("⚠️  Please change the password in production!")
    else:
        logger.error("❌ Failed to create admin user")


async def create_test_user():
    """Create a test user"""
    db = await get_database()
    
    # Check if test user already exists
    existing_user = await db.users.find_one({"username": "testuser"})
    if existing_user:
        logger.info("✅ Test user already exists!")
        return
    
    # Create test user data
    test_user_data = {
        "username": "testuser",
        "email": "test@fifa-tracker.com",
        "first_name": "Test",
        "last_name": "User",
        "hashed_password": get_password_hash("test123"),
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(datetime.UTC),
        "updated_at": datetime.now(datetime.UTC),
        # Initialize player statistics
        "total_matches": 0,
        "total_goals_scored": 0,
        "total_goals_conceded": 0,
        "goal_difference": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "points": 0
    }
    
    # Insert test user
    result = await db.users.insert_one(test_user_data)
    
    if result.inserted_id:
        logger.info("✅ Test user created successfully!")
        logger.info("Username: testuser")
        logger.info("Password: test123")
    else:
        logger.error("❌ Failed to create test user")


async def main():
    """Main function"""
    logger.info("🚀 Creating default users for FIFA Rivalry Tracker...")
    
    try:
        await create_admin_user()
        await create_test_user()
        logger.info("🎉 User creation completed!")
        logger.info("You can now:")
        logger.info("1. Login at /api/v1/auth/login")
        logger.info("2. Register new users at /api/v1/auth/register")
        logger.info("3. Access protected endpoints with JWT tokens")
        
    except Exception as e:
        logger.error(f"❌ Error creating users: {str(e)}")
        logger.error("Make sure your MongoDB connection is working and .env file is configured.")


if __name__ == "__main__":
    asyncio.run(main()) 