#!/usr/bin/env python3
"""
Migration script to update existing users' last_5_teams field to use unique teams.
This script will:
1. Update all existing users' last_5_teams field to contain only unique teams
2. Re-populate the field with unique teams from their recent matches
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


async def update_unique_teams():
    """Update existing users to use unique teams in last_5_teams field"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.DATABASE_NAME]
    
    try:
        print("Starting update: Converting last_5_teams to unique teams...")
        
        # Get all users
        users = await db.users.find({}).to_list(length=None)
        print(f"Found {len(users)} users to update")
        
        updated_count = 0
        
        for user in users:
            user_id = user["_id"]
            username = user.get("username", "Unknown")
            
            # Check if user has last_5_teams field
            if "last_5_teams" not in user:
                print(f"User {username} doesn't have last_5_teams field, skipping...")
                continue
            
            current_teams = user.get("last_5_teams", [])
            
            # Get user's recent matches to re-populate with unique teams
            recent_matches = await db.matches.find({
                "$or": [
                    {"player1_id": str(user_id)},
                    {"player2_id": str(user_id)}
                ]
            }).sort("date", -1).limit(20).to_list(length=20)  # Get more matches to ensure we have enough unique teams
            
            # Extract unique teams from recent matches
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
            
            # Update user with unique teams
            await db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "last_5_teams": teams,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            updated_count += 1
            print(f"Updated user {username}: {len(current_teams)} -> {len(teams)} unique teams")
        
        print(f"Update completed successfully! Updated {updated_count} users.")
        
    except Exception as e:
        print(f"Update failed with error: {e}")
        raise
    finally:
        client.close()


async def main():
    """Main function to run the update"""
    print("=" * 60)
    print("FIFA Rivalry Tracker - Unique Teams Update")
    print("=" * 60)
    print(f"Database: {settings.DATABASE_NAME}")
    print(f"MongoDB URL: {settings.MONGO_URI}")
    print(f"Timestamp: {datetime.utcnow()}")
    print("=" * 60)
    
    # Confirm before proceeding (skip in non-interactive mode)
    import sys
    if sys.stdin.isatty():
        response = input("Do you want to proceed with the update? (y/N): ")
        if response.lower() != 'y':
            print("Update cancelled.")
            return
    else:
        print("Running in non-interactive mode, proceeding with update...")
    
    await update_unique_teams()


if __name__ == "__main__":
    asyncio.run(main())
