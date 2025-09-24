from typing import List
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from itertools import groupby
from datetime import datetime

from app.models import Player, PlayerDetailedStats, Match
from app.models.auth import UserInDB, UserCreate, UserUpdate
from app.api.dependencies import get_database
from app.utils.helpers import match_helper
from app.utils.auth import get_current_active_user, user_helper, get_password_hash

router = APIRouter()

@router.post("/", response_model=Player)
async def register_player(player: UserCreate, current_user: UserInDB = Depends(get_current_active_user)):
    """Register a new player (user)"""
    db = await get_database()
    existing_player = await db.users.find_one({"username": player.username})
    if existing_player:
        raise HTTPException(
            status_code=400, detail="A player with this username already exists"
        )

    # Check if email already exists
    existing_email = await db.users.find_one({"email": player.email})
    if existing_email:
        raise HTTPException(
            status_code=400, detail="Email already registered"
        )

    from datetime import datetime
    from app.utils.auth import get_password_hash
    
    player_data = player.dict()
    player_data.update({
        "hashed_password": get_password_hash(player.password),
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
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
        "tournament_ids": [],
        # Friend system fields
        "friends": [],
        "friend_requests_sent": [],
        "friend_requests_received": []
    })
    
    # Remove plain password from data
    del player_data["password"]
    
    new_player = await db.users.insert_one(player_data)
    created_player = await db.users.find_one({"_id": new_player.inserted_id})
    return user_helper(created_player)


@router.get("/", response_model=List[Player])
async def get_players(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all active players (excluding deleted ones)"""
    db = await get_database()
    players = await db.users.find({"is_deleted": {"$ne": True}}).to_list(1000)
    return [user_helper(player) for player in players]


@router.get("/{player_id}", response_model=Player)
async def get_player(player_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get a specific player by ID (including deleted players)"""
    db = await get_database()
    try:
        player = await db.users.find_one({"_id": ObjectId(player_id)})
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        return user_helper(player)
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid player ID format")
        raise HTTPException(status_code=404, detail="Player not found")


@router.put("/{player_id}", response_model=Player)
async def update_player(player_id: str, player: UserUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    """Update a player's information (partial update - only provided fields will be updated)"""
    db = await get_database()
    # Check if player exists
    existing_player = await db.users.find_one({"_id": ObjectId(player_id)})
    if not existing_player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Check if player is deleted
    if existing_player.get("is_deleted", False):
        raise HTTPException(status_code=400, detail="Cannot update a deleted player")

    # Check if new username already exists (if different from current)
    if player.username is not None and player.username != existing_player.get("username"):
        existing_username = await db.users.find_one({"username": player.username})
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already exists")

    # Check if new email already exists (if different from current)
    if player.email is not None and player.email != existing_player.get("email"):
        existing_email = await db.users.find_one({"email": player.email})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

    # Update player data
    update_data = {}
    if player.username is not None:
        update_data["username"] = player.username
    if player.email is not None:
        update_data["email"] = player.email
    if player.first_name is not None:
        update_data["first_name"] = player.first_name
    if player.last_name is not None:
        update_data["last_name"] = player.last_name

    # Check if any fields are being updated
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()
    
    update_result = await db.users.update_one(
        {"_id": ObjectId(player_id)},
        {"$set": update_data}
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Player update failed")

    # Get updated player
    updated_player = await db.users.find_one({"_id": ObjectId(player_id)})
    return user_helper(updated_player)


@router.delete("/{player_id}", response_model=dict)
async def delete_player(player_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Mark a player as deleted instead of actually deleting them"""
    db = await get_database()
    try:
        # Check if player exists
        player = await db.users.find_one({"_id": ObjectId(player_id)})
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        # Mark player as deleted instead of actually deleting
        update_data = {
            "is_active": False,
            "is_deleted": True,
            "deleted_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        update_result = await db.users.update_one(
            {"_id": ObjectId(player_id)},
            {"$set": update_data}
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Player deletion failed")

        return {"message": "Player marked as deleted successfully"}
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid player ID format")
        raise


@router.get("/{player_id}/stats", response_model=PlayerDetailedStats)
async def get_player_detailed_stats(player_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get detailed statistics for a specific player (including deleted players)"""
    db = await get_database()
    player : Player = await db.users.find_one({"_id": ObjectId(player_id)})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get all matches for this player
    matches: List[Match] = await db.matches.find({
        "$or": [
            {"player1_id": player_id},
            {"player2_id": player_id}
        ]
    }).sort("date", 1).to_list(1000)

    wins_against = {}
    losses_against = {}

    for match in matches:
        opponent_id = (
            match["player2_id"]
            if match["player1_id"] == player_id
            else match["player1_id"]
        )
        opponent : Player = await db.users.find_one({"_id": ObjectId(opponent_id)})

        if match["player1_id"] == player_id:
            if match["player1_goals"] > match["player2_goals"]:
                wins_against[opponent["username"]] = (
                    wins_against.get(opponent["username"], 0) + 1
                )
            elif match["player1_goals"] < match["player2_goals"]:
                losses_against[opponent["username"]] = (
                    losses_against.get(opponent["username"], 0) + 1
                )
        else:
            if match["player2_goals"] > match["player1_goals"]:
                wins_against[opponent["username"]] = (
                    wins_against.get(opponent["username"], 0) + 1
                )
            elif match["player2_goals"] < match["player1_goals"]:
                losses_against[opponent["username"]] = (
                    losses_against.get(opponent["username"], 0) + 1
                )

    highest_wins = (
        max(wins_against.items(), key=lambda x: x[1]) if wins_against else None
    )
    highest_losses = (
        max(losses_against.items(), key=lambda x: x[1]) if losses_against else None
    )

    # Calculate winrate over time (per day)
    total_matches = 0
    total_wins = 0
    daily_winrate = []

    # Convert match dates to datetime objects if they're strings
    for match in matches:
        if isinstance(match["date"], str):
            match["date"] = datetime.fromisoformat(match["date"])

    # Group matches by date
    for date, day_matches in groupby(matches, key=lambda x: x["date"].date()):
        day_matches = list(day_matches)
        for match in day_matches:
            total_matches += 1
            is_player1 = match["player1_id"] == player_id
            player_goals = (
                match["player1_goals"] if is_player1 else match["player2_goals"]
            )
            opponent_goals = (
                match["player2_goals"] if is_player1 else match["player1_goals"]
            )

            if player_goals > opponent_goals:
                total_wins += 1

        winrate = total_wins / total_matches if total_matches > 0 else 0
        # Convert date to datetime at midnight
        date_dt = datetime.combine(date, datetime.min.time())
        daily_winrate.append({"date": date_dt, "winrate": winrate})

    # Calculate tournament participation
    tournaments_played = 0
    tournament_ids = []
    
    # Find all tournaments where this player is a participant
    tournaments = await db.tournaments.find({
        "player_ids": {"$in": [player_id]}
    }).to_list(1000)
    
    tournaments_played = len(tournaments)
    tournament_ids = [str(t["_id"]) for t in tournaments]
    
    stats = user_helper(player)
    stats.update(
        {
            "win_rate": (
                player["wins"] / player["total_matches"]
                if player["total_matches"] > 0
                else 0
            ),
            "average_goals_scored": (
                player["total_goals_scored"] / player["total_matches"]
                if player["total_matches"] > 0
                else 0
            ),
            "average_goals_conceded": (
                player["total_goals_conceded"] / player["total_matches"]
                if player["total_matches"] > 0
                else 0
            ),
            "highest_wins_against": (
                {highest_wins[0]: highest_wins[1]} if highest_wins else None
            ),
            "highest_losses_against": (
                {highest_losses[0]: highest_losses[1]} if highest_losses else None
            ),
            "winrate_over_time": daily_winrate,
            "tournaments_played": tournaments_played,
            "tournament_ids": tournament_ids,
        }
    )

    return PlayerDetailedStats(**stats)


@router.get("/{player_id}/matches")
async def get_player_matches(player_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get all matches for a specific player (including deleted players)"""
    db = await get_database()
    
    # Get player info
    player : Player = await db.users.find_one({"_id": ObjectId(player_id)})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    matches = (
        await db.matches.find(
            {"$or": [{"player1_id": player_id}, {"player2_id": player_id}]}
        )
        .sort("date", -1)
        .to_list(1000)
    )

    # Return matches with player names
    matches_with_names = []
    for match in matches:
        match_data = await match_helper(match, db)
        matches_with_names.append(match_data)

    return matches_with_names
