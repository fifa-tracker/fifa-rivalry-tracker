from datetime import datetime
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

def player_helper(player) -> dict:
    """Convert player document to dict format"""
    return {
        "id": str(player["_id"]),
        "name": player["name"],
        "total_matches": player["total_matches"],
        "total_goals_scored": player["total_goals_scored"],
        "total_goals_conceded": player["total_goals_conceded"],
        "goal_difference": player["goal_difference"],
        "wins": player["wins"],
        "losses": player["losses"],
        "draws": player["draws"],
        "points": player["points"],
    }


async def match_helper(match, db) -> dict:
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
        player1 = await db.players.find_one({"_id": ObjectId(player1_id)})
        player2 = await db.players.find_one({"_id": ObjectId(player2_id)})
        
        player1_name = player1["name"] if player1 else "Unknown Player"
        player2_name = player2["name"] if player2 else "Unknown Player"
        
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
            tournament = await db.tournaments.find_one({"_id": ObjectId(match["tournament_id"])})
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
