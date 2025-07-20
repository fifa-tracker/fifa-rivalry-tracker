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
from datetime import datetime


async def create_admin_user():
    """Create a default admin user"""
    db = await get_database()
    
    # Check if admin user already exists
    existing_admin = await db.users.find_one({"username": "admin"})
    if existing_admin:
        print("✅ Admin user already exists!")
        return
    
    # Create admin user data
    admin_data = {
        "username": "admin",
        "email": "admin@fifa-tracker.com",
        "full_name": "Administrator",
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
        print("✅ Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("⚠️  Please change the password in production!")
    else:
        print("❌ Failed to create admin user")


async def create_test_user():
    """Create a test user"""
    db = await get_database()
    
    # Check if test user already exists
    existing_user = await db.users.find_one({"username": "testuser"})
    if existing_user:
        print("✅ Test user already exists!")
        return
    
    # Create test user data
    test_user_data = {
        "username": "testuser",
        "email": "test@fifa-tracker.com",
        "full_name": "Test User",
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
        print("✅ Test user created successfully!")
        print("Username: testuser")
        print("Password: test123")
    else:
        print("❌ Failed to create test user")


async def main():
    """Main function"""
    print("🚀 Creating default users for FIFA Rivalry Tracker...")
    
    try:
        await create_admin_user()
        await create_test_user()
        print("\n🎉 User creation completed!")
        print("\nYou can now:")
        print("1. Login at /api/v1/auth/login")
        print("2. Register new users at /api/v1/auth/register")
        print("3. Access protected endpoints with JWT tokens")
        
    except Exception as e:
        print(f"❌ Error creating users: {str(e)}")
        print("Make sure your MongoDB connection is working and .env file is configured.")


if __name__ == "__main__":
    asyncio.run(main()) 