import os
from datetime import datetime
from itertools import groupby
from typing import Dict, List, Optional, Union
import pathlib

from bson import ObjectId 
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from dotenv import load_dotenv

from app.schemas.player import PlayerCreate, Player, PlayerDetailedStats
from app.schemas.match import MatchCreate, Match, MatchUpdate, HeadToHeadStats
from app.schemas.tournament import TournamentCreate, Tournament

# Load environment variables from .env file
env_path = pathlib.Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable pymongo debug logs
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("motor").setLevel(logging.WARNING)

app = FastAPI()

# Determine environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
logger.info(f"Running in {ENVIRONMENT} environment")

# MongoDB connection URIs
MONGODB_URI = {
    "development": "mongodb://localhost:27017/fifa_rivalry",
    "production": "mongodb://mongodb:27017/fifa_rivalry",
}

# Get the appropriate MongoDB URI based on environment
mongo_uri = os.getenv(f"MONGO_URI_{ENVIRONMENT.upper()}", os.getenv("MONGO_URI", MONGODB_URI[ENVIRONMENT]))
logger.info(f"Using MongoDB URI: {mongo_uri}")

# Connect to MongoDB
client = AsyncIOMotorClient(mongo_uri)
db = client.fifa_rivalry

# Log connection status
logger.info(f"Connected to MongoDB at {client.address if client else 'Not connected'}")

# Helper functions
def player_helper(player) -> dict:
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


async def match_helper(match) -> dict:
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


@app.post("/players", response_model=Player)
async def register_player(player: PlayerCreate):
    existing_player = await db.players.find_one({"name": player.name})
    if existing_player:
        raise HTTPException(
            status_code=400, detail="A player with this name already exists"
        )

    player_data = {
        "name": player.name,
        "total_matches": 0,
        "total_goals_scored": 0,
        "total_goals_conceded": 0,
        "goal_difference": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "points": 0
    }
    new_player = await db.players.insert_one(player_data)
    created_player = await db.players.find_one({"_id": new_player.inserted_id})
    return Player(**player_helper(created_player))


@app.post("/matches", response_model=Match)
async def record_match(match: MatchCreate):
    player1 = await db.players.find_one({"_id": ObjectId(match.player1_id)})
    player2 = await db.players.find_one({"_id": ObjectId(match.player2_id)})

    if not player1 or not player2:
        raise HTTPException(status_code=404, detail="One or both players not found")

    match_dict = {
        "player1_id": match.player1_id,
        "player2_id": match.player2_id,
        "player1_goals": match.player1_goals,
        "player2_goals": match.player2_goals,
        "team1": match.team1,
        "team2": match.team2,
        "tournament_id": match.tournament_id,
        "date": datetime.now()
    }
    new_match = await db.matches.insert_one(match_dict)

    # Update player stats
    for player, goals_scored, goals_conceded in [
        (player1, match.player1_goals, match.player2_goals),
        (player2, match.player2_goals, match.player1_goals),
    ]:
        update = {
            "$inc": {
                "total_matches": 1,
                "total_goals_scored": goals_scored,
                "total_goals_conceded": goals_conceded,
                "goal_difference": goals_scored - goals_conceded,
            }
        }

        if goals_scored > goals_conceded:
            update["$inc"]["wins"] = 1
            update["$inc"]["points"] = 3
        elif goals_scored < goals_conceded:
            update["$inc"]["losses"] = 1
        else:
            update["$inc"]["draws"] = 1
            update["$inc"]["points"] = 1

        await db.players.update_one({"_id": player["_id"]}, update)

    created_match = await db.matches.find_one({"_id": new_match.inserted_id})
    return Match(**await match_helper(created_match))


@app.get("/players", response_model=List[Player])
async def get_players():
    players = await db.players.find().to_list(length=None)
    return [Player(**player_helper(player)) for player in players]


@app.get("/stats", response_model=List[Player])
async def get_stats():
    players = await db.players.find().sort("points", -1).to_list(length=None)
    return [Player(**player_helper(player)) for player in players]


@app.get("/matches", response_model=List[Match])
async def get_matches():
    matches = await db.matches.find().sort("date", -1).to_list(length=None)
    return [Match(**await match_helper(match)) for match in matches]


@app.get("/player/{player_id}/matches", response_model=List[Match])
async def get_player_matches(player_id: str):
    matches = await db.matches.find({
        "$or": [
            {"player1_id": player_id},
            {"player2_id": player_id}
        ]
    }).sort("date", -1).to_list(length=None)
    return [Match(**await match_helper(match)) for match in matches]


@app.get("/head-to-head/{player1_id}/{player2_id}", response_model=HeadToHeadStats)
async def get_head_to_head_stats(player1_id: str, player2_id: str):
    player1 = await db.players.find_one({"_id": ObjectId(player1_id)})
    player2 = await db.players.find_one({"_id": ObjectId(player2_id)})

    if not player1 or not player2:
        raise HTTPException(status_code=404, detail="One or both players not found")

    matches = await db.matches.find({
        "$or": [
            {"$and": [{"player1_id": player1_id}, {"player2_id": player2_id}]},
            {"$and": [{"player1_id": player2_id}, {"player2_id": player1_id}]}
        ]
    }).to_list(length=None)

    total_matches = len(matches)
    player1_wins = 0
    player2_wins = 0
    draws = 0
    player1_goals = 0
    player2_goals = 0

    for match in matches:
        if match["player1_id"] == player1_id:
            p1_goals = match["player1_goals"]
            p2_goals = match["player2_goals"]
        else:
            p1_goals = match["player2_goals"]
            p2_goals = match["player1_goals"]

        player1_goals += p1_goals
        player2_goals += p2_goals

        if p1_goals > p2_goals:
            player1_wins += 1
        elif p1_goals < p2_goals:
            player2_wins += 1
        else:
            draws += 1

    player1_win_rate = player1_wins / total_matches if total_matches > 0 else 0
    player2_win_rate = player2_wins / total_matches if total_matches > 0 else 0
    player1_avg_goals = player1_goals / total_matches if total_matches > 0 else 0
    player2_avg_goals = player2_goals / total_matches if total_matches > 0 else 0

    return HeadToHeadStats(
        player1_name=player1["name"],
        player2_name=player2["name"],
        total_matches=total_matches,
        player1_wins=player1_wins,
        player2_wins=player2_wins,
        draws=draws,
        player1_goals=player1_goals,
        player2_goals=player2_goals,
        player1_win_rate=player1_win_rate,
        player2_win_rate=player2_win_rate,
        player1_avg_goals=player1_avg_goals,
        player2_avg_goals=player2_avg_goals
    )


@app.get("/player/{player_id}/stats", response_model=PlayerDetailedStats)
async def get_player_detailed_stats(player_id: str):
    player = await db.players.find_one({"_id": ObjectId(player_id)})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    matches = await db.matches.find({
        "$or": [
            {"player1_id": player_id},
            {"player2_id": player_id}
        ]
    }).sort("date", 1).to_list(length=None)

    # Calculate win rate over time
    winrate_over_time = []
    total_matches = 0
    total_wins = 0

    for match in matches:
        total_matches += 1
        if match["player1_id"] == player_id:
            if match["player1_goals"] > match["player2_goals"]:
                total_wins += 1
        else:
            if match["player2_goals"] > match["player1_goals"]:
                total_wins += 1

        win_rate = total_wins / total_matches if total_matches > 0 else 0
        winrate_over_time.append({
            "date": match["date"],
            "win_rate": win_rate
        })

    # Calculate highest wins/losses against
    opponents = {}
    for match in matches:
        if match["player1_id"] == player_id:
            opponent_id = match["player2_id"]
            is_win = match["player1_goals"] > match["player2_goals"]
            is_loss = match["player1_goals"] < match["player2_goals"]
        else:
            opponent_id = match["player1_id"]
            is_win = match["player2_goals"] > match["player1_goals"]
            is_loss = match["player2_goals"] < match["player1_goals"]

        if opponent_id not in opponents:
            opponents[opponent_id] = {"wins": 0, "losses": 0}

        if is_win:
            opponents[opponent_id]["wins"] += 1
        elif is_loss:
            opponents[opponent_id]["losses"] += 1

    highest_wins_against = {}
    highest_losses_against = {}

    for opponent_id, stats in opponents.items():
        opponent = await db.players.find_one({"_id": ObjectId(opponent_id)})
        if opponent:
            if stats["wins"] > 0:
                highest_wins_against[opponent["name"]] = stats["wins"]
            if stats["losses"] > 0:
                highest_losses_against[opponent["name"]] = stats["losses"]

    return PlayerDetailedStats(
        id=str(player["_id"]),
        name=player["name"],
        total_matches=player["total_matches"],
        total_goals_scored=player["total_goals_scored"],
        total_goals_conceded=player["total_goals_conceded"],
        wins=player["wins"],
        losses=player["losses"],
        draws=player["draws"],
        points=player["points"],
        win_rate=player["wins"] / player["total_matches"] if player["total_matches"] > 0 else 0,
        average_goals_scored=player["total_goals_scored"] / player["total_matches"] if player["total_matches"] > 0 else 0,
        average_goals_conceded=player["total_goals_conceded"] / player["total_matches"] if player["total_matches"] > 0 else 0,
        highest_wins_against=highest_wins_against,
        highest_losses_against=highest_losses_against,
        winrate_over_time=winrate_over_time
    )

@app.delete("/player/{player_id}", response_model=dict)
async def delete_player(player_id: str):
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
    await db.players.delete_one({"_id": ObjectId(player_id)})

    return {"message": "Player and associated matches deleted successfully"}

@app.put("/player/{player_id}", response_model=Player)
async def update_player(player_id: str, player: PlayerCreate):
    existing_player = await db.players.find_one({"_id": ObjectId(player_id)})
    if not existing_player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Check if new name is already taken by another player
    name_taken = await db.players.find_one({
        "name": player.name,
        "_id": {"$ne": ObjectId(player_id)}
    })
    if name_taken:
        raise HTTPException(status_code=400, detail="A player with this name already exists")

    await db.players.update_one(
        {"_id": ObjectId(player_id)},
        {"$set": {"name": player.name}}
    )

    updated_player = await db.players.find_one({"_id": ObjectId(player_id)})
    return Player(**player_helper(updated_player))

@app.put("/matches/{match_id}", response_model=Match)
async def update_match(match_id: str, match_update: MatchUpdate):
    match = await db.matches.find_one({"_id": ObjectId(match_id)})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Get the original match data
    player1_id = match["player1_id"]
    player2_id = match["player2_id"]
    old_player1_goals = match["player1_goals"]
    old_player2_goals = match["player2_goals"]

    # Update the match
    await db.matches.update_one(
        {"_id": ObjectId(match_id)},
        {
            "$set": {
                "player1_goals": match_update.player1_goals,
                "player2_goals": match_update.player2_goals
            }
        }
    )

    # Update player stats by reversing old results and applying new ones
    for player_id, old_goals_scored, old_goals_conceded, new_goals_scored, new_goals_conceded in [
        (player1_id, old_player1_goals, old_player2_goals, match_update.player1_goals, match_update.player2_goals),
        (player2_id, old_player2_goals, old_player1_goals, match_update.player2_goals, match_update.player1_goals)
    ]:
        # Reverse old stats
        update = {
            "$inc": {
                "total_goals_scored": -old_goals_scored,
                "total_goals_conceded": -old_goals_conceded,
                "goal_difference": -(old_goals_scored - old_goals_conceded)
            }
        }

        if old_goals_scored > old_goals_conceded:
            update["$inc"]["wins"] = -1
            update["$inc"]["points"] = -3
        elif old_goals_scored < old_goals_conceded:
            update["$inc"]["losses"] = -1
        else:
            update["$inc"]["draws"] = -1
            update["$inc"]["points"] = -1

        await db.players.update_one({"_id": ObjectId(player_id)}, update)

        # Apply new stats
        update = {
            "$inc": {
                "total_goals_scored": new_goals_scored,
                "total_goals_conceded": new_goals_conceded,
                "goal_difference": new_goals_scored - new_goals_conceded
            }
        }

        if new_goals_scored > new_goals_conceded:
            update["$inc"]["wins"] = 1
            update["$inc"]["points"] = 3
        elif new_goals_scored < new_goals_conceded:
            update["$inc"]["losses"] = 1
        else:
            update["$inc"]["draws"] = 1
            update["$inc"]["points"] = 1

        await db.players.update_one({"_id": ObjectId(player_id)}, update)

    updated_match = await db.matches.find_one({"_id": ObjectId(match_id)})
    return Match(**await match_helper(updated_match))

@app.delete("/matches/{match_id}", response_model=dict)
async def delete_match(match_id: str):
    match = await db.matches.find_one({"_id": ObjectId(match_id)})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Update player stats by reversing the match results
    for player_id, goals_scored, goals_conceded in [
        (match["player1_id"], match["player1_goals"], match["player2_goals"]),
        (match["player2_id"], match["player2_goals"], match["player1_goals"])
    ]:
        update = {
            "$inc": {
                "total_matches": -1,
                "total_goals_scored": -goals_scored,
                "total_goals_conceded": -goals_conceded,
                "goal_difference": -(goals_scored - goals_conceded)
            }
        }

        if goals_scored > goals_conceded:
            update["$inc"]["wins"] = -1
            update["$inc"]["points"] = -3
        elif goals_scored < goals_conceded:
            update["$inc"]["losses"] = -1
        else:
            update["$inc"]["draws"] = -1
            update["$inc"]["points"] = -1

        await db.players.update_one({"_id": ObjectId(player_id)}, update)

    # Delete the match
    await db.matches.delete_one({"_id": ObjectId(match_id)})

    return {"message": "Match deleted successfully"}

@app.post("/tournaments", response_model=Tournament)
async def create_tournament(tournament: TournamentCreate):
    tournament_data = {
        "name": tournament.name,
        "start_date": tournament.start_date,
        "end_date": tournament.end_date,
        "description": tournament.description,
        "matches_count": 0
    }
    new_tournament = await db.tournaments.insert_one(tournament_data)
    created_tournament = await db.tournaments.find_one({"_id": new_tournament.inserted_id})
    return Tournament(
        id=str(created_tournament["_id"]),
        name=created_tournament["name"],
        start_date=created_tournament["start_date"],
        end_date=created_tournament["end_date"],
        description=created_tournament.get("description"),
        matches_count=created_tournament["matches_count"]
    )

@app.get("/tournaments", response_model=List[Tournament])
async def get_tournaments():
    tournaments = await db.tournaments.find().sort("start_date", -1).to_list(length=None)
    return [
        Tournament(
            id=str(t["_id"]),
            name=t["name"],
            start_date=t["start_date"],
            end_date=t["end_date"],
            description=t.get("description"),
            matches_count=t["matches_count"]
        ) for t in tournaments
    ]

@app.get("/tournaments/{tournament_id}/matches", response_model=List[Match])
async def get_tournament_matches(tournament_id: str):
    matches = await db.matches.find({"tournament_id": tournament_id}).sort("date", -1).to_list(length=None)
    return [Match(**await match_helper(match)) for match in matches]

@app.get("/")
async def home():
    return {"message": "Welcome to the FIFA Rivalry Tracker API"}

