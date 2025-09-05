#!/usr/bin/env python3
"""
Script to create specific rivalry tracker users.
Creates users: roshatron, shinigami, and kAMi with password "password"
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.api.dependencies import get_database
from app.utils.auth import get_password_hash
from app.utils.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)


async def create_user(username: str, email: str, first_name: str, last_name: str = "", is_superuser: bool = False):
    """Create a user with the specified details"""
    db = await get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"username": username})
    if existing_user:
        logger.info(f"✅ User '{username}' already exists!")
        return
    
    # Create user data
    user_data = {
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "hashed_password": get_password_hash("password"),
        "is_active": True,
        "is_superuser": is_superuser,
        "is_deleted": False,
        "created_at": datetime.now(datetime.UTC),
        "updated_at": datetime.now(datetime.UTC),
        "deleted_at": None,
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
    
    # Insert user
    result = await db.users.insert_one(user_data)
    
    if result.inserted_id:
        logger.info(f"✅ User '{username}' created successfully!")
        logger.info(f"   Email: {email}")
        logger.info(f"   Password: password")
        logger.info(f"   Superuser: {is_superuser}")
    else:
        logger.error(f"❌ Failed to create user '{username}'")


async def main():
    """Main function to create rivalry users"""
    logger.info("🚀 Creating FIFA Rivalry Tracker users...")
    
    try:
        # Create the three specified users
        await create_user(
            username="roshatron",
            email="roshatron@fifa-tracker.com",
            first_name="Roshan",
            last_name="",
            is_superuser=True  # Making roshatron a superuser
        )
        
        await create_user(
            username="shinigami",
            email="shinigami@fifa-tracker.com",
            first_name="Shinigami",
            last_name="",
            is_superuser=False
        )
        
        await create_user(
            username="kAMi",
            email="kami@fifa-tracker.com",
            first_name="kAMi",
            last_name="",
            is_superuser=False
        )
        
        logger.info("🎉 All rivalry users created successfully!")
        logger.info("📋 Summary:")
        logger.info("   - roshatron (Superuser)")
        logger.info("   - shinigami")
        logger.info("   - kAMi")
        logger.info("   All users have password: 'password'")
        logger.info("")
        logger.info("You can now:")
        logger.info("1. Login at /api/v1/auth/login with any of these users")
        logger.info("2. Use JWT tokens to access protected endpoints")
        logger.warning("⚠️  Consider changing passwords in production!")
        
    except Exception as e:
        logger.error(f"❌ Error creating users: {str(e)}")
        logger.error("Make sure your MongoDB connection is working and .env file is configured.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
