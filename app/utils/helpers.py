from datetime import datetime
from bson import ObjectId
import logging
from app.models import Player, Match, Tournament
from typing import List

logger = logging.getLogger(__name__)




async def match_helper(match : Match, db) -> dict:
    """Convert match document to dict format with player names"""
    try:
        # Get player information
        player1_id = match.get("player1_id")
        player2_id = match.get("player2_id")
        
        if not player1_id or not player2_id:
            logger.error(f"Match missing player IDs: {match.get('_id')}")
            return {
                "id": str(match["_id"]),
                "player1_name": "Unknown Player",
                "player2_name": "Unknown Player",
                "player1_goals": match.get("player1_goals", 0),
                "player2_goals": match.get("player2_goals", 0),
                "date": match.get("date", datetime.now()),
                "team1": match.get("team1", "Unknown"),
                "team2": match.get("team2", "Unknown"),
            }
        
        # Find players
        player1 : Player = await db.users.find_one({"_id": ObjectId(player1_id)})
        player2 : Player = await db.users.find_one({"_id": ObjectId(player2_id)})
        
        player1_name = player1["username"] if player1 else "Unknown Player"
        player2_name = player2["username"] if player2 else "Unknown Player"
        
        result = {
            "id": str(match["_id"]),
            "player1_name": player1_name,
            "player2_name": player2_name,
            "player1_goals": match.get("player1_goals", 0),
            "player2_goals": match.get("player2_goals", 0),
            "date": match.get("date", datetime.now()),
            "team1": match.get("team1", "Unknown"),
            "team2": match.get("team2", "Unknown"),
        }
        
        # Add tournament info if available
        if match.get("tournament_id"):
            tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(match["tournament_id"])})
            if tournament:
                result["tournament_name"] = tournament["name"]
        
        return result
    except Exception as e:
        logger.error(f"Error in match_helper: {str(e)}")
        # Return a minimal valid response
        return {
            "id": str(match.get("_id", "unknown")),
            "player1_name": "Error",
            "player2_name": "Error",
            "player1_goals": 0,
            "player2_goals": 0,
            "date": datetime.now(),
        }


def get_result(player1_goals, player2_goals, is_player1):
    """Calculate win/loss/draw result for a player"""
    if is_player1:
        if player1_goals > player2_goals:
            return {"win": 1, "loss": 0, "draw": 0}
        elif player1_goals < player2_goals:
            return {"win": 0, "loss": 1, "draw": 0}
        else:
            return {"win": 0, "loss": 0, "draw": 1}
    else:
        if player2_goals > player1_goals:
            return {"win": 1, "loss": 0, "draw": 0}
        elif player2_goals < player1_goals:
            return {"win": 0, "loss": 1, "draw": 0}
        else:
            return {"win": 0, "loss": 0, "draw": 1}


def calculate_tournament_stats(player_id: str, matches: List[dict]) -> dict:
    """Calculate tournament statistics for a specific player based on match data"""
    stats = {
        "total_matches": 0,
        "total_goals_scored": 0,
        "total_goals_conceded": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "points": 0
    }
    
    for match in matches:
        player1_id = match.get("player1_id")
        player2_id = match.get("player2_id")
        player1_goals = match.get("player1_goals", 0)
        player2_goals = match.get("player2_goals", 0)
        
        # Convert ObjectIds to strings for comparison
        player1_id_str = str(player1_id) if player1_id else None
        player2_id_str = str(player2_id) if player2_id else None
        
        # Skip matches where this player is not involved
        if player_id not in [player1_id_str, player2_id_str]:
            continue
            
        stats["total_matches"] += 1
        
        # Determine if this player is player1 or player2
        is_player1 = player_id == player1_id_str
        
        if is_player1:
            stats["total_goals_scored"] += player1_goals
            stats["total_goals_conceded"] += player2_goals
            result = get_result(player1_goals, player2_goals, True)
        else:
            stats["total_goals_scored"] += player2_goals
            stats["total_goals_conceded"] += player1_goals
            result = get_result(player1_goals, player2_goals, False)
        
        stats["wins"] += result["win"]
        stats["losses"] += result["loss"]
        stats["draws"] += result["draw"]
        
        # Calculate points (3 for win, 1 for draw, 0 for loss)
        stats["points"] += (result["win"] * 3) + (result["draw"] * 1)
    
    # Calculate goal difference
    stats["goal_difference"] = stats["total_goals_scored"] - stats["total_goals_conceded"]
    
    return stats
