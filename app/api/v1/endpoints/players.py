from typing import List
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from itertools import groupby
from datetime import datetime

from app.models import PlayerCreate, Player, PlayerDetailedStats, Match
from app.api.dependencies import get_database
from app.utils.helpers import player_helper

router = APIRouter()

@router.post("/", response_model=Player)
async def register_player(player: PlayerCreate):
    """Register a new player"""
    db = await get_database()
    existing_player = await db.players.find_one({"name": player.name})
    if existing_player:
        raise HTTPException(
            status_code=400, detail="A player with this name already exists"
        )

    player_data = player.dict()
    player_data.update({
        "total_matches": 0,
        "total_goals_scored": 0,
        "total_goals_conceded": 0,
        "goal_difference": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "points": 0
    })
    new_player = await db.players.insert_one(player_data)
    created_player = await db.players.find_one({"_id": new_player.inserted_id})
    return player_helper(created_player)


@router.get("/", response_model=List[Player])
async def get_players():
    """Get all players"""
    db = await get_database()
    players = await db.players.find().to_list(1000)
    return [player_helper(player) for player in players]


@router.get("/{player_id}", response_model=Player)
async def get_player(player_id: str):
    """Get a specific player by ID"""
    db = await get_database()
    try:
        player = await db.players.find_one({"_id": ObjectId(player_id)})
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        return player_helper(player)
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid player ID format")
        raise HTTPException(status_code=404, detail="Player not found")


@router.put("/{player_id}", response_model=Player)
async def update_player(player_id: str, player: PlayerCreate):
    """Update a player's name"""
    db = await get_database()
    # Check if player exists
    existing_player = await db.players.find_one({"_id": ObjectId(player_id)})
    if not existing_player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Update player name
    update_result = await db.players.update_one(
        {"_id": ObjectId(player_id)},
        {"$set": {"name": player.name}}
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Player update failed")

    # Get updated player
    updated_player = await db.players.find_one({"_id": ObjectId(player_id)})
    return player_helper(updated_player)


@router.delete("/{player_id}", response_model=dict)
async def delete_player(player_id: str):
    """Delete a player and all their matches"""
    db = await get_database()
    try:
        # Check if player exists
        player = await db.players.find_one({"_id": ObjectId(player_id)})
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        # Delete all matches involving this player
        await db.matches.delete_many({
            "$or": [
                {"player1_id": player_id},
                {"player2_id": player_id}
            ]
        })

        # Delete the player
        delete_result = await db.players.delete_one({"_id": ObjectId(player_id)})
        
        if delete_result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Player deletion failed")

        return {"message": "Player and associated matches deleted successfully"}
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid player ID format")
        raise


@router.get("/{player_id}/stats", response_model=PlayerDetailedStats)
async def get_player_detailed_stats(player_id: str):
    """Get detailed statistics for a specific player"""
    db = await get_database()
    player : Player = await db.players.find_one({"_id": ObjectId(player_id)})
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
        opponent : Player = await db.players.find_one({"_id": ObjectId(opponent_id)})

        if match["player1_id"] == player_id:
            if match["player1_goals"] > match["player2_goals"]:
                wins_against[opponent["name"]] = (
                    wins_against.get(opponent["name"], 0) + 1
                )
            elif match["player1_goals"] < match["player2_goals"]:
                losses_against[opponent["name"]] = (
                    losses_against.get(opponent["name"], 0) + 1
                )
        else:
            if match["player2_goals"] > match["player1_goals"]:
                wins_against[opponent["name"]] = (
                    wins_against.get(opponent["name"], 0) + 1
                )
            elif match["player2_goals"] < match["player1_goals"]:
                losses_against[opponent["name"]] = (
                    losses_against.get(opponent["name"], 0) + 1
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

    stats = player_helper(player)
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
        }
    )

    return PlayerDetailedStats(**stats)


@router.get("/{player_id}/matches")
async def get_player_matches(player_id: str):
    """Get all matches for a specific player"""
    db = await get_database()
    
    # Get player info
    player : Player = await db.players.find_one({"_id": ObjectId(player_id)})
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
