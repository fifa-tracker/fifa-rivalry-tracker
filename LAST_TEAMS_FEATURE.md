# Last 5 Teams Feature

This document describes the new `last_5_teams` field that has been added to the user model.

## Overview

Each user now has a `last_5_teams` field that tracks the last 5 **unique** teams they have played with in matches. This field is automatically updated whenever a user plays a match.

## Field Details

- **Field Name**: `last_5_teams`
- **Type**: `List[str]`
- **Default Value**: `[]` (empty list)
- **Maximum Length**: 5 unique teams
- **Update Behavior**: 
  - If the team already exists in the list, it's moved to the front (most recent position)
  - If it's a new team, it's added to the front
  - Only unique teams are kept (no duplicates)
  - Oldest teams are removed when the list exceeds 5 unique teams

## Implementation

### Database Schema
The field is added to the `User` model in `app/models/auth.py`:

```python
last_5_teams: List[str] = []  # List of last 5 teams the user has played with
```

### User Creation
When a new user is created, the `last_5_teams` field is initialized as an empty list in both:
- `app/api/v1/endpoints/auth.py` (user registration)
- `app/api/v1/endpoints/players.py` (player registration)

### Match Recording
When a match is recorded in `app/api/v1/endpoints/matches.py`, the system:
1. Extracts the team played by each player (`team1` for player1, `team2` for player2)
2. If the team already exists in the player's `last_5_teams` list, removes it first
3. Adds the team to the beginning of the player's `last_5_teams` list (most recent position)
4. Truncates the list to keep only the last 5 unique teams
5. Updates the player's record in the database

### Migration
For existing users, run the migration script:

```bash
python scripts/migrate_last_teams.py
```

This script will:
- Add the `last_5_teams` field to all existing users
- Populate the field with unique teams from their recent matches (up to 5 unique teams)
- Update the `updated_at` timestamp

## API Response

The `last_5_teams` field is included in all user/player API responses:

```json
{
  "id": "user_id",
  "username": "player1",
  "last_5_teams": ["Barcelona", "Real Madrid", "Arsenal", "Chelsea", "Liverpool"],
  ...
}
```

## Testing

The feature is covered by tests in:
- `app/tests/test_players.py`: Verifies field initialization
- `app/tests/test_matches.py`: Verifies field updates and 5-team limit

## Usage Examples

### Getting a user's recent unique teams
```python
# The last_5_teams field shows the most recent unique teams first
user = get_user_by_id(user_id)
recent_teams = user.last_5_teams
# Example: ["Barcelona", "Real Madrid", "Arsenal", "Chelsea", "Liverpool"]
# Note: Each team appears only once, even if played multiple times
```

### Tracking team usage patterns
```python
# Check if a user has played with a specific team recently
def has_played_with_team_recently(user, team_name):
    return team_name in user.last_5_teams

# Get the most recently played team
def get_most_recent_team(user):
    return user.last_5_teams[0] if user.last_5_teams else None
```

### Example: Duplicate team handling
```python
# If a user plays with Barcelona multiple times:
# Before: ["Real Madrid", "Arsenal", "Chelsea", "Liverpool", "PSG"]
# After playing Barcelona: ["Barcelona", "Real Madrid", "Arsenal", "Chelsea", "Liverpool"]
# Barcelona moves to the front, PSG is removed (oldest)
```
