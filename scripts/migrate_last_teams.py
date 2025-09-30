#!/usr/bin/env python3
"""
Migration script to add last_5_teams field to existing users.
This script will:
1. Add the last_5_teams field to all existing users
2. Populate the field with teams from their recent matches (if any)
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


async def migrate_last_teams():
    """Migrate existing users to include last_5_teams field"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.DATABASE_NAME]
    
    try:
        print("Starting migration: Adding last_5_teams field to existing users...")
        
        # Get all users
        users = await db.users.find({}).to_list(length=None)
        print(f"Found {len(users)} users to migrate")
        
        migrated_count = 0
        
        for user in users:
            user_id = user["_id"]
            username = user.get("username", "Unknown")
            
            # Check if user already has last_5_teams field
            if "last_5_teams" in user:
                print(f"User {username} already has last_5_teams field, skipping...")
                continue
            
            # Get user's recent matches to populate last_5_teams
            recent_matches = await db.matches.find({
                "$or": [
                    {"player1_id": str(user_id)},
                    {"player2_id": str(user_id)}
                ]
            }).sort("date", -1).limit(5).to_list(length=5)
            
            # Extract teams from recent matches (keeping only unique teams)
            teams = []
            seen_teams = set()
            for match in recent_matches:
                team = None
                if match.get("player1_id") == str(user_id) and match.get("team1"):
                    team = match["team1"]
                elif match.get("player2_id") == str(user_id) and match.get("team2"):
                    team = match["team2"]
                
                if team and team not in seen_teams:
                    teams.append(team)
                    seen_teams.add(team)
                    if len(teams) >= 5:  # Stop at 5 unique teams
                        break
            
            # Update user with last_5_teams field
            await db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "last_5_teams": teams,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            migrated_count += 1
            print(f"Migrated user {username}: {len(teams)} teams found")
        
        print(f"Migration completed successfully! Migrated {migrated_count} users.")
        
    except Exception as e:
        print(f"Migration failed with error: {e}")
        raise
    finally:
        client.close()


async def main():
    """Main function to run the migration"""
    print("=" * 60)
    print("FIFA Rivalry Tracker - Last Teams Migration")
    print("=" * 60)
    print(f"Database: {settings.DATABASE_NAME}")
    print(f"MongoDB URL: {settings.MONGO_URI}")
    print(f"Timestamp: {datetime.utcnow()}")
    print("=" * 60)
    
    # Confirm before proceeding (skip in non-interactive mode)
    import sys
    if sys.stdin.isatty():
        response = input("Do you want to proceed with the migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
    else:
        print("Running in non-interactive mode, proceeding with migration...")
    
    await migrate_last_teams()


if __name__ == "__main__":
    asyncio.run(main())
