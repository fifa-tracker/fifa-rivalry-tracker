# Name Field Migration

This document describes the migration from a single `name` field to separate `first_name` and `last_name` fields in the FIFA Rivalry Tracker application.

## Overview

The application has been updated to split the user's name field into two separate fields:
- `first_name`: The user's first name
- `last_name`: The user's last name (including middle names, prefixes, etc.)

## Changes Made

### 1. Model Updates

**File: `app/models/auth.py`**
- Updated `UserBase`, `UserCreate`, `UserUpdate`, `User`, `UserInDB`, and `UserDetailedStats` models
- Replaced `name: Optional[str] = None` with:
  - `first_name: Optional[str] = None`
  - `last_name: Optional[str] = None`

**File: `app/models/tournament.py`**
- Updated `TournamentPlayerStats` model
- Replaced `name: Optional[str] = None` with:
  - `first_name: Optional[str] = None`
  - `last_name: Optional[str] = None`

### 2. Utility Function Updates

**File: `app/utils/auth.py`**
- Updated `get_current_user()` function to handle new field structure
- Updated `user_helper()` function to return `first_name` and `last_name` instead of `name`

### 3. API Endpoint Updates

**File: `app/api/v1/endpoints/players.py`**
- Updated player update endpoint to handle `first_name` and `last_name` fields

**File: `app/api/v1/endpoints/tournaments.py`**
- Updated tournament player stats to use `first_name` and `last_name` fields

### 4. Test Updates

**Files: `app/tests/test_stats.py`, `app/tests/test_players.py`, `conftest.py`**
- Updated test data to use new field structure
- Fixed assertions to use `username` instead of `name` where appropriate

### 5. Script Updates

**File: `scripts/create_admin_user.py`**
- Updated to use `first_name` and `last_name` fields

## Migration Script

### Main Migration Script: `scripts/migrate_name_fields.py`

This script will:
1. Find all users with a `name` field
2. Split the name into `first_name` and `last_name`
3. Update the database records
4. Remove the old `name` field

#### Usage

```bash
# Make sure you're in the project root directory
cd /path/to/fifa-rivalry-tracker

# Run the migration
python scripts/migrate_name_fields.py
```

#### Name Splitting Logic

The script handles various name formats:
- `"John Doe"` → `first_name: "John"`, `last_name: "Doe"`
- `"John"` → `first_name: "John"`, `last_name: ""`
- `"John van Doe"` → `first_name: "John"`, `last_name: "van Doe"`
- `"John van der Doe"` → `first_name: "John"`, `last_name: "van der Doe"`

### Test Script: `scripts/test_migration.py`

This script tests the migration process:
1. Creates a test user with a `name` field
2. Runs the migration
3. Verifies the results
4. Cleans up test data

#### Usage

```bash
# Test the migration
python scripts/test_migration.py
```

## Database Schema Changes

### Before Migration
```javascript
{
  "_id": ObjectId,
  "username": "string",
  "email": "string",
  "name": "string",  // Single name field
  "hashed_password": "string",
  // ... other fields
}
```

### After Migration
```javascript
{
  "_id": ObjectId,
  "username": "string",
  "email": "string",
  "first_name": "string",  // First name only
  "last_name": "string",   // Last name (including middle names, prefixes)
  "hashed_password": "string",
  // ... other fields
}
```

## API Changes

### User Registration
**Before:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "name": "John Doe",
  "password": "password123"
}
```

**After:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "password123"
}
```

### User Update
**Before:**
```json
{
  "name": "John van der Doe"
}
```

**After:**
```json
{
  "first_name": "John",
  "last_name": "van der Doe"
}
```

## Migration Steps

### 1. Backup Your Database
Before running the migration, make sure to backup your MongoDB database:

```bash
# Backup your database
mongodump --uri="your_mongodb_connection_string" --db=fifa_rivalry
```

### 2. Deploy Code Changes
Deploy the updated code to your environment.

### 3. Run the Migration
```bash
python scripts/migrate_name_fields.py
```

### 4. Verify the Migration
```bash
python scripts/test_migration.py
```

### 5. Test Your Application
Run your application tests to ensure everything works correctly.

## Rollback Plan

If you need to rollback the migration:

1. **Database Rollback**: Restore from your backup
2. **Code Rollback**: Revert to the previous version of the code
3. **Redeploy**: Deploy the previous version

## Notes

- The migration is designed to be safe and non-destructive
- It will only modify users that have a `name` field
- Users without a `name` field will remain unchanged
- The script provides detailed logging of the migration process
- The migration can be run multiple times safely (it will skip already migrated users)

## Troubleshooting

### Common Issues

1. **Permission Errors**: Make sure the script has read/write access to the database
2. **Connection Errors**: Verify your MongoDB connection string in the environment variables
3. **Import Errors**: Make sure you're running the script from the project root directory

### Logs

The migration script provides detailed logging:
- ✅ Successfully migrated users
- ⚠️ Skipped users (no changes needed)
- ❌ Errors during migration

Check the logs to identify any issues during the migration process. 