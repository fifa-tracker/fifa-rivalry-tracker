#!/usr/bin/env python3
"""
Script to migrate existing users' name field to first_name and last_name fields.
This script will:
1. Find all users with a 'name' field
2. Split the name into first_name and last_name
3. Update the database records
4. Remove the old 'name' field
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.api.dependencies import get_database
from app.utils.logging import get_logger

logger = get_logger(__name__)


def split_name(full_name: str) -> tuple[str, str]:
    """
    Split a full name into first name and last name.
    Handles various name formats:
    - "John Doe" -> ("John", "Doe")
    - "John" -> ("John", "")
    - "John van Doe" -> ("John", "van Doe")
    - "John van der Doe" -> ("John", "van der Doe")
    """
    if not full_name or not full_name.strip():
        return "", ""
    
    name_parts = full_name.strip().split()
    
    if len(name_parts) == 0:
        return "", ""
    elif len(name_parts) == 1:
        return name_parts[0], ""
    else:
        # First name is the first part
        first_name = name_parts[0]
        # Last name is everything else
        last_name = " ".join(name_parts[1:])
        return first_name, last_name


async def migrate_user_names():
    """Migrate all users' name fields to first_name and last_name"""
    db = await get_database()
    
    # Find all users that have a 'name' field
    users_with_name = await db.users.find({"name": {"$exists": True}}).to_list(length=None)
    
    if not users_with_name:
        logger.info("✅ No users found with 'name' field. Migration not needed.")
        return
    
    logger.info(f"📋 Found {len(users_with_name)} users with 'name' field to migrate")
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    for user in users_with_name:
        try:
            user_id = user["_id"]
            username = user.get("username", "unknown")
            old_name = user.get("name", "")
            
            # Split the name
            first_name, last_name = split_name(old_name)
            
            # Prepare update data
            update_data = {
                "first_name": first_name,
                "last_name": last_name,
                "updated_at": datetime.utcnow()
            }
            
            # Update the user document
            result = await db.users.update_one(
                {"_id": user_id},
                {
                    "$set": update_data,
                    "$unset": {"name": ""}  # Remove the old name field
                }
            )
            
            if result.modified_count > 0:
                migrated_count += 1
                logger.info(f"✅ Migrated user '{username}': '{old_name}' -> '{first_name}' '{last_name}'")
            else:
                skipped_count += 1
                logger.warning(f"⚠️  No changes made for user '{username}'")
                
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Error migrating user '{username}': {str(e)}")
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 MIGRATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total users processed: {len(users_with_name)}")
    logger.info(f"Successfully migrated: {migrated_count}")
    logger.info(f"Skipped: {skipped_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("=" * 50)


async def verify_migration():
    """Verify that the migration was successful"""
    db = await get_database()
    
    # Check for users with old 'name' field
    users_with_old_name = await db.users.find({"name": {"$exists": True}}).to_list(length=None)
    
    if users_with_old_name:
        logger.warning(f"⚠️  Found {len(users_with_old_name)} users still with 'name' field:")
        for user in users_with_old_name:
            logger.warning(f"  - {user.get('username', 'unknown')}: {user.get('name', '')}")
    else:
        logger.info("✅ No users found with old 'name' field")
    
    # Check for users with new fields
    users_with_new_fields = await db.users.find({
        "$or": [
            {"first_name": {"$exists": True}},
            {"last_name": {"$exists": True}}
        ]
    }).to_list(length=None)
    
    logger.info(f"📋 Found {len(users_with_new_fields)} users with new name fields")
    
    # Show some examples
    if users_with_new_fields:
        logger.info("📝 Sample migrated users:")
        for user in users_with_new_fields[:5]:  # Show first 5
            username = user.get("username", "unknown")
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            logger.info(f"  - {username}: '{first_name}' '{last_name}'")


async def main():
    """Main function"""
    try:
        logger.info("🚀 Starting name field migration...")
        
        # Run the migration
        await migrate_user_names()
        
        # Verify the migration
        logger.info("\n🔍 Verifying migration...")
        await verify_migration()
        
        logger.info("\n✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 