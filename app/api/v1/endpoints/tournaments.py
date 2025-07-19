from typing import List
import logging
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from pydantic import BaseModel

from app.models import TournamentCreate, Tournament, Match, Player
from app.api.dependencies import get_database
from app.utils.helpers import match_helper, player_helper, calculate_tournament_stats

logger = logging.getLogger(__name__)

router = APIRouter()

def tournament_helper(tournament : Tournament):
    result = {
        "id": str(tournament["_id"]),
        **{k: v for k, v in tournament.items() if k != "_id"}
    }
    
    # Convert ObjectId matches to strings
    if "matches" in result and result["matches"]:
        result["matches"] = [str(match_id) for match_id in result["matches"]]
    
    # Convert ObjectId player_ids to strings if they exist
    if "player_ids" in result and result["player_ids"]:
        result["player_ids"] = [str(player_id) for player_id in result["player_ids"]]
    
    return result

class PlayerIdRequest(BaseModel):
    player_id: str

@router.post("/", response_model=Tournament)
async def create_tournament(tournament: TournamentCreate):
    """Create a new tournament"""
    db = await get_database()
    # Convert to dict with default values
    tournament_dict = tournament.model_dump()
    tournament_dict["matches"] = []
    tournament_dict["matches_count"] = 0
    new_tournament = await db.tournaments.insert_one(tournament_dict)
    created_tournament = await db.tournaments.find_one({"_id": new_tournament.inserted_id})
    return Tournament(**tournament_helper(created_tournament))

@router.get("/", response_model=List[Tournament])
async def get_tournaments():
    """Get all tournaments"""
    db = await get_database()
    tournaments : List[Tournament] = await db.tournaments.find().to_list(1000)
    return [Tournament(**tournament_helper(t)) for t in tournaments]

@router.get("/{tournament_id}/matches", response_model=List[Match])
async def get_tournament_matches(tournament_id: str):
    """Get all matches for a specific tournament"""
    db = await get_database()
    matches : List[Match] = await db.matches.find({"tournament_id": tournament_id}).sort("date", -1).to_list(1000)
    return [Match(**await match_helper(match, db)) for match in matches]

@router.get("/{tournament_id}/", response_model=Tournament)
async def get_tournament(tournament_id: str):
    """Get a specific tournament"""
    db = await get_database()
    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return Tournament(**tournament_helper(tournament))

@router.post("/{tournament_id}/players", response_model=Tournament)
async def add_player_to_tournament(tournament_id: str, player_request: PlayerIdRequest):
    """Add a player to a tournament"""
    db = await get_database()
    logger.info(f"Adding player {player_request.player_id} to tournament {tournament_id}")
    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Initialize player_ids if it doesn't exist
    if "player_ids" not in tournament:
        tournament["player_ids"] = []
    
    # Check if player is already in tournament
    if player_request.player_id in tournament["player_ids"]:
        raise HTTPException(status_code=400, detail="Player already in tournament")
    
    tournament["player_ids"].append(player_request.player_id)
    await db.tournaments.update_one({"_id": ObjectId(tournament_id)}, {"$set": {"player_ids": tournament["player_ids"]}})
    return Tournament(**tournament_helper(tournament))

@router.delete("/{tournament_id}/players/{player_id}", response_model=Tournament)
async def remove_player_from_tournament(tournament_id: str, player_id: str):
    """Remove a player from a tournament"""
    db = await get_database()
    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Initialize player_ids if it doesn't exist
    if "player_ids" not in tournament:
        tournament["player_ids"] = []
    
    if player_id not in tournament["player_ids"]:
        raise HTTPException(status_code=404, detail="Player not found in tournament")
    tournament["player_ids"].remove(player_id)
    await db.tournaments.update_one({"_id": ObjectId(tournament_id)}, {"$set": {"player_ids": tournament["player_ids"]}})
    return Tournament(**tournament_helper(tournament))

@router.get("/{tournament_id}/stats", response_model=List[Player])
async def get_tournament_stats(tournament_id: str):
    """Get tournament stats"""
    db = await get_database()
    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    logger.info(f"Tournament: {tournament} \n")
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Handle player_ids - they might be stored as strings or ObjectIds
    player_ids = tournament.get("player_ids", [])
    logger.info(f"Player IDs from tournament: {player_ids}")
    
    if not player_ids:
        logger.warning("No players found in tournament")
        return []
    
    # Convert string IDs to ObjectIds for database query
    try:
        player_object_ids = [ObjectId(pid) if isinstance(pid, str) else pid for pid in player_ids]
        players : List[Player] = await db.players.find({"_id": {"$in": player_object_ids}}).to_list(1000)
        logger.info(f"Found {len(players)} players in database")
    except Exception as e:
        logger.error(f"Error converting player IDs: {e}")
        return []
    
    matches : List[Match] = await db.matches.find({"tournament_id": tournament_id}).to_list(1000)
    logger.info(f"Found {len(matches)} matches for tournament")
    
    if not players:
        logger.warning("No players found in database")
        return []
    
    if not matches:
        logger.info("No matches found for tournament, returning empty stats")
        # Return players with zero stats
        tournament_stats = []
        for player in players:
            player_stats = {
                "id": str(player["_id"]),
                "name": player["name"],
                "total_matches": 0,
                "total_goals_scored": 0,
                "total_goals_conceded": 0,
                "goal_difference": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "points": 0
            }
            tournament_stats.append(player_stats)
        return tournament_stats

    # Calculate tournament statistics for each player
    tournament_stats = []
    for player in players:
        player_id = str(player["_id"])
        logger.info(f"Calculating stats for player {player['name']} (ID: {player_id})")
        stats = calculate_tournament_stats(player_id, matches)
        
        # Create player stats object with tournament-specific data
        player_stats = {
            "id": player_id,
            "name": player["name"],
            "total_matches": stats["total_matches"],
            "total_goals_scored": stats["total_goals_scored"],
            "total_goals_conceded": stats["total_goals_conceded"],
            "goal_difference": stats["goal_difference"],
            "wins": stats["wins"],
            "losses": stats["losses"],
            "draws": stats["draws"],
            "points": stats["points"]
        }
        
        tournament_stats.append(player_stats)
        logger.info(f"Player {player['name']} tournament stats: {stats}")

    # Sort by points in descending order (highest points first)
    tournament_stats.sort(key=lambda x: x["points"], reverse=True)
    
    return tournament_stats

@router.post("/tournament/{tournament_id}/match", response_model=Tournament)
async def add_match_to_tournament(tournament_id: str, match: Match):
    """Add a match to a tournament"""
    db = await get_database()
    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    await db.matches.insert_one(match.model_dump())
    await db.tournaments.update_one({"_id": ObjectId(tournament_id)}, {"$set": {"matches_count": tournament["matches_count"] + 1}})
    tournament["matches_count"] = tournament["matches_count"] + 1
    return Tournament(**tournament_helper(tournament))