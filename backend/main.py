
import logging
from fastapi import FastAPI
from app.api.v1.router import api_router
from app.api.dependencies import client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FIFA Rivalry Tracker API",
    description="API for tracking FIFA match results and player statistics",
    version="1.0.0"
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Test the actual connection
@app.on_event("startup")
async def startup_event():
    try:
        # This will actually test the connection
        await client.admin.command('ping')
        logger.info("✅ MongoDB Atlas connection successful!")
    except Exception as e:
        logger.error(f"❌ MongoDB Atlas connection failed: {str(e)}")
        logger.error("Please check:")
        logger.error("1. Your internet connection")
        logger.error("2. MongoDB Atlas IP whitelist settings")
        logger.error("3. Username and password in connection string")
        logger.error("4. Database name in connection string")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "FIFA Rivalry Tracker API", 
        "version": "1.0.0",
        "docs": "/docs"
    }

# import os
# from datetime import datetime
# from itertools import groupby
# from typing import Dict, List, Optional, Union
# import pathlib

# from bson import ObjectId 
# from fastapi import FastAPI, HTTPException
# from motor.motor_asyncio import AsyncIOMotorClient
# from pydantic import BaseModel, Field
# import logging
# from dotenv import dotenv_values

# # Import models from the new models package
# from app.models import (
#     PlayerCreate, Player, PlayerDetailedStats,
#     MatchCreate, Match, MatchUpdate, HeadToHeadStats,
#     TournamentCreate, Tournament
# )

# # Load environment variables from .env file
# env_path = pathlib.Path(__file__).parent / '.env'
# config = dotenv_values(env_path)

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Disable pymongo debug logs
# # logging.getLogger("pymongo").setLevel(logging.WARNING)
# # logging.getLogger("motor").setLevel(logging.WARNING)

# app = FastAPI()

# # Determine environment from .env file
# ENVIRONMENT = config.get("ENVIRONMENT", "development")
# logger.info(f"Running in {ENVIRONMENT} environment")


# # Get MongoDB URI from .env file or use default based on environment
# mongo_uri = config.get("MONGO_URI") or config.get(f"MONGO_URI_{ENVIRONMENT.upper()}")
# logger.info(f"Using MongoDB URI: {mongo_uri}")

# # Connect to MongoDB
# client = AsyncIOMotorClient(mongo_uri)
# db = client.fifa_rivalry

# # Log connection status
# logger.info(f"Connected to MongoDB at {client.address if client else 'Not connected'}")

# # Test the actual connection
# @app.on_event("startup")
# async def startup_event():
#     try:
#         # This will actually test the connection
#         await client.admin.command('ping')
#         logger.info("✅ MongoDB Atlas connection successful!")
#     except Exception as e:
#         logger.error(f"❌ MongoDB Atlas connection failed: {str(e)}")
#         logger.error("Please check:")
#         logger.error("1. Your internet connection")
#         logger.error("2. MongoDB Atlas IP whitelist settings")
#         logger.error("3. Username and password in connection string")
#         logger.error("4. Database name in connection string")

# # Helper functions
# def player_helper(player) -> dict:
#     return {
#         "id": str(player["_id"]),
#         "name": player["name"],
#         "total_matches": player["total_matches"],
#         "total_goals_scored": player["total_goals_scored"],
#         "total_goals_conceded": player["total_goals_conceded"],
#         "goal_difference": player["goal_difference"],
#         "wins": player["wins"],
#         "losses": player["losses"],
#         "draws": player["draws"],
#         "points": player["points"],
#     }


# async def match_helper(match) -> dict:
#     try:
#         # Get player information
#         player1_id = match.get("player1_id")
#         player2_id = match.get("player2_id")
        
#         if not player1_id or not player2_id:
#             logger.error(f"Match missing player IDs: {match.get('_id')}")
#             return {
#                 "id": str(match["_id"]),
#                 "player1_name": "Unknown Player",
#                 "player2_name": "Unknown Player",
#                 "player1_goals": match.get("player1_goals", 0),
#                 "player2_goals": match.get("player2_goals", 0),
#                 "date": match.get("date", datetime.now()),
#                 "team1": match.get("team1", "Unknown"),
#                 "team2": match.get("team2", "Unknown"),
#             }
        
#         # Find players
#         player1 = await db.players.find_one({"_id": ObjectId(player1_id)})
#         player2 = await db.players.find_one({"_id": ObjectId(player2_id)})
        
#         player1_name = player1["name"] if player1 else "Unknown Player"
#         player2_name = player2["name"] if player2 else "Unknown Player"
        
#         result = {
#             "id": str(match["_id"]),
#             "player1_name": player1_name,
#             "player2_name": player2_name,
#             "player1_goals": match.get("player1_goals", 0),
#             "player2_goals": match.get("player2_goals", 0),
#             "date": match.get("date", datetime.now()),
#             "team1": match.get("team1", "Unknown"),
#             "team2": match.get("team2", "Unknown"),
#         }
        
#         # Add tournament info if available
#         if match.get("tournament_id"):
#             tournament = await db.tournaments.find_one({"_id": ObjectId(match["tournament_id"])})
#             if tournament:
#                 result["tournament_name"] = tournament["name"]
        
#         return result
#     except Exception as e:
#         logger.error(f"Error in match_helper: {str(e)}")
#         # Return a minimal valid response
#         return {
#             "id": str(match.get("_id", "unknown")),
#             "player1_name": "Error",
#             "player2_name": "Error",
#             "player1_goals": 0,
#             "player2_goals": 0,
#             "date": datetime.now(),
#         }


# @app.post("/players", response_model=Player)
# async def register_player(player: PlayerCreate):
#     existing_player = await db.players.find_one({"name": player.name})
#     if existing_player:
#         raise HTTPException(
#             status_code=400, detail="A player with this name already exists"
#         )

#     player_data = player.dict()
#     player_data.update({
#         "total_matches": 0,
#         "total_goals_scored": 0,
#         "total_goals_conceded": 0,
#         "goal_difference": 0,
#         "wins": 0,
#         "losses": 0,
#         "draws": 0,
#         "points": 0
#     })
#     new_player = await db.players.insert_one(player_data)
#     created_player = await db.players.find_one({"_id": new_player.inserted_id})
#     return player_helper(created_player)


# @app.post("/matches", response_model=Match)
# async def record_match(match: MatchCreate):
#     player1 = await db.players.find_one({"_id": ObjectId(match.player1_id)})
#     player2 = await db.players.find_one({"_id": ObjectId(match.player2_id)})

#     if not player1 or not player2:
#         raise HTTPException(status_code=404, detail="One or both players not found")

#     match_dict = match.dict()
#     match_dict["date"] = datetime.now()
#     new_match = await db.matches.insert_one(match_dict)

#     # Update player stats
#     for player, goals_scored, goals_conceded in [
#         (player1, match.player1_goals, match.player2_goals),
#         (player2, match.player2_goals, match.player1_goals),
#     ]:
#         update = {
#             "$inc": {
#                 "total_matches": 1,
#                 "total_goals_scored": goals_scored,
#                 "total_goals_conceded": goals_conceded,
#                 "goal_difference" : goals_scored - goals_conceded,
#                 "wins": 1 if goals_scored > goals_conceded else 0,
#                 "losses": 1 if goals_scored < goals_conceded else 0,
#                 "draws": 1 if goals_scored == goals_conceded else 0,
#                 "points": (
#                     3
#                     if goals_scored > goals_conceded
#                     else (1 if goals_scored == goals_conceded else 0)
#                 ),
#             }
#         }
#         await db.players.update_one({"_id": player["_id"]}, update)

#     created_match = await db.matches.find_one({"_id": new_match.inserted_id})
#     return Match(**await match_helper(created_match))


# @app.get("/players", response_model=List[Player])
# async def get_players():
#     players = await db.players.find().to_list(1000)
#     return [player_helper(player) for player in players]


# @app.get("/players/{player_id}", response_model=Player)
# async def get_player(player_id: str):
#     try:
#         player = await db.players.find_one({"_id": ObjectId(player_id)})
#         if not player:
#             raise HTTPException(status_code=404, detail="Player not found")
#         return Player(**player_helper(player))
#     except Exception as e:
#         if "Invalid ObjectId" in str(e):
#             raise HTTPException(status_code=400, detail="Invalid player ID format")
#         raise HTTPException(status_code=404, detail="Player not found")


# @app.get("/stats", response_model=List[Player])
# async def get_stats():
#     players = await db.players.find().sort([("points", -1), ("goal_difference", -1)]).to_list(1000)
#     logger.info([player_helper(player) for player in players])

#     return [player_helper(player) for player in players]


# @app.get("/matches", response_model=List[Match])
# async def get_matches():
#     matches = await db.matches.find().sort("date", -1).to_list(1000)
#     return [Match(**await match_helper(match)) for match in matches]


# @app.get("/player/{player_id}/matches", response_model=List[Match])
# async def get_player_matches(player_id: str):
#     matches = (
#         await db.matches.find(
#             {"$or": [{"player1_id": player_id}, {"player2_id": player_id}]}
#         )
#         .sort("date", -1)
#         .to_list(1000)
#     )
#     return [Match(**await match_helper(match)) for match in matches]


# @app.get("/head-to-head/{player1_id}/{player2_id}", response_model=HeadToHeadStats)
# async def get_head_to_head_stats(player1_id: str, player2_id: str):
#     player1 = await db.players.find_one({"_id": ObjectId(player1_id)})
#     player2 = await db.players.find_one({"_id": ObjectId(player2_id)})

#     if not player1 or not player2:
#         raise HTTPException(status_code=404, detail="One or both players not found")

#     matches = await db.matches.find(
#         {
#             "$or": [
#                 {"player1_id": player1_id, "player2_id": player2_id},
#                 {"player1_id": player2_id, "player2_id": player1_id},
#             ]
#         }
#     ).to_list(1000)

#     stats = {
#         "player1_name": player1["name"],
#         "player2_name": player2["name"],
#         "total_matches": len(matches),
#         "player1_wins": 0,
#         "player2_wins": 0,
#         "draws": 0,
#         "player1_goals": 0,
#         "player2_goals": 0,
#     }

#     for match in matches:
#         if match["player1_id"] == player1_id:
#             stats["player1_goals"] += match["player1_goals"]
#             stats["player2_goals"] += match["player2_goals"]
#             if match["player1_goals"] > match["player2_goals"]:
#                 stats["player1_wins"] += 1
#             elif match["player1_goals"] < match["player2_goals"]:
#                 stats["player2_wins"] += 1
#             else:
#                 stats["draws"] += 1
#         else:
#             stats["player1_goals"] += match["player2_goals"]
#             stats["player2_goals"] += match["player1_goals"]
#             if match["player1_goals"] < match["player2_goals"]:
#                 stats["player1_wins"] += 1
#             elif match["player1_goals"] > match["player2_goals"]:
#                 stats["player2_wins"] += 1
#             else:
#                 stats["draws"] += 1

#     # Calculate win rates and average goals
#     stats["player1_win_rate"] = (
#         stats["player1_wins"] / stats["total_matches"]
#         if stats["total_matches"] > 0
#         else 0
#     )
#     stats["player2_win_rate"] = (
#         stats["player2_wins"] / stats["total_matches"]
#         if stats["total_matches"] > 0
#         else 0
#     )
#     stats["player1_avg_goals"] = (
#         stats["player1_goals"] / stats["total_matches"]
#         if stats["total_matches"] > 0
#         else 0
#     )
#     stats["player2_avg_goals"] = (
#         stats["player2_goals"] / stats["total_matches"]
#         if stats["total_matches"] > 0
#         else 0
#     )

#     return HeadToHeadStats(**stats)


# @app.get("/player/{player_id}/stats", response_model=PlayerDetailedStats)
# async def get_player_detailed_stats(player_id: str):
#     player = await db.players.find_one({"_id": ObjectId(player_id)})
#     if not player:
#         raise HTTPException(status_code=404, detail="Player not found")

#     

# @app.delete("/player/{player_id}", response_model=dict)
# async def delete_player(player_id: str):
#     try:
        
#         # Check if player exists
#         player = await db.players.find_one({"_id": ObjectId(player_id)})
        
#         if not player:
#             raise HTTPException(status_code=404, detail="Player not found")

#         # Delete all matches involving this player
#         delete_matches = await db.matches.delete_many({
#             "$or": [
#                 {"player1_id": player_id},
#                 {"player2_id": player_id}
#             ]
#         })

#         # Delete the player
#         delete_result = await db.players.delete_one({"_id": ObjectId(player_id)})
        
#         if delete_result.deleted_count == 0:
#             raise HTTPException(status_code=400, detail="Player deletion failed")

#         return {"message": "Player and associated matches deleted successfully"}
#     except Exception as e:
#         logger.error(f"Error deleting player: {str(e)}")
#         if "Invalid ObjectId" in str(e):
#             raise HTTPException(status_code=400, detail="Invalid player ID format")
#         raise

# @app.put("/player/{player_id}", response_model=Player)
# async def update_player(player_id: str, player: PlayerCreate):
#     # Check if player exists
#     existing_player = await db.players.find_one({"_id": ObjectId(player_id)})
#     if not existing_player:
#         raise HTTPException(status_code=404, detail="Player not found")

#     # Update player name
#     update_result = await db.players.update_one(
#         {"_id": ObjectId(player_id)},
#         {"$set": {"name": player.name}}
#     )

#     if update_result.modified_count == 0:
#         raise HTTPException(status_code=400, detail="Player update failed")

#     # Get updated player
#     updated_player = await db.players.find_one({"_id": ObjectId(player_id)})
#     return Player(**player_helper(updated_player))

# @app.put("/matches/{match_id}", response_model=Match)
# async def update_match(match_id: str, match_update: MatchUpdate):
#     try:
#         # Validate match_id format
#         if not ObjectId.is_valid(match_id):
#             logger.error(f"Invalid match ID format: {match_id}")
#             raise HTTPException(status_code=400, detail="Invalid match ID format")

#         # Find the match
#         match = await db.matches.find_one({"_id": ObjectId(match_id)})
        
#         if not match:
#             logger.error(f"Match not found: {match_id}")
#             raise HTTPException(status_code=404, detail="Match not found")

#         # Validate goals are non-negative
#         if match_update.player1_goals < 0 or match_update.player2_goals < 0:
#             raise HTTPException(status_code=400, detail="Goals cannot be negative")

#         # Calculate the changes in goals
#         player1_goals_diff = match_update.player1_goals - match["player1_goals"]
#         player2_goals_diff = match_update.player2_goals - match["player2_goals"]

#         # Check if there are any actual changes
#         if player1_goals_diff == 0 and player2_goals_diff == 0:
#             # Return the current match data without updating
#             return Match(**await match_helper(match))

#         # Update match
#         update_result = await db.matches.update_one(
#             {"_id": ObjectId(match_id)},
#             {
#                 "$set": {
#                     "player1_goals": match_update.player1_goals,
#                     "player2_goals": match_update.player2_goals,
#                 }
#             },
#         )

#         if update_result.matched_count == 0:
#             logger.error(f"Match update failed: {update_result}")
#             raise HTTPException(status_code=400, detail="Match update failed - match not found")

#         # Update player stats
#         for player_id, goals_diff, opponent_goals_diff in [
#             (match["player1_id"], player1_goals_diff, player2_goals_diff),
#             (match["player2_id"], player2_goals_diff, player1_goals_diff),
#         ]:
#             if not ObjectId.is_valid(player_id):
#                 logger.error(f"Invalid player ID format: {player_id}")
#                 continue

#             player = await db.players.find_one({"_id": ObjectId(player_id)})
#             if not player:
#                 logger.error(f"Player not found: {player_id}")
#                 continue

#             # Calculate win/loss/draw changes
#             old_result = get_result(
#                 match["player1_goals"],
#                 match["player2_goals"],
#                 player_id == match["player1_id"],
#             )
#             new_result = get_result(
#                 match_update.player1_goals,
#                 match_update.player2_goals,
#                 player_id == match["player1_id"],
#             )

#             wins_diff = new_result["win"] - old_result["win"]
#             losses_diff = new_result["loss"] - old_result["loss"]
#             draws_diff = new_result["draw"] - old_result["draw"]

#             # Skip player update if there are no changes
#             if goals_diff == 0 and opponent_goals_diff == 0 and wins_diff == 0 and losses_diff == 0 and draws_diff == 0:
#                 continue

#             # Update player stats
#             await db.players.update_one(
#                 {"_id": ObjectId(player_id)},
#                 {
#                     "$inc": {
#                         "total_goals_scored": goals_diff,
#                         "total_goals_conceded": opponent_goals_diff,
#                         "goal_difference": goals_diff - opponent_goals_diff,
#                         "wins": wins_diff,
#                         "losses": losses_diff,
#                         "draws": draws_diff,
#                         "points": wins_diff * 3 + draws_diff,
#                     }
#                 },
#             )

#         # Fetch updated match
#         updated_match = await db.matches.find_one({"_id": ObjectId(match_id)})
#         if not updated_match:
#             logger.error(f"Updated match not found")
#             raise HTTPException(status_code=404, detail="Updated match not found")
        
#         return Match(**await match_helper(updated_match))

#     except Exception as e:
#         logger.error(f"Error updating match: {str(e)}")
#         if "Invalid ObjectId" in str(e):
#             raise HTTPException(status_code=400, detail="Invalid ID format")
#         raise HTTPException(status_code=400, detail=str(e))


# def get_result(player1_goals, player2_goals, is_player1):
#     if is_player1:
#         if player1_goals > player2_goals:
#             return {"win": 1, "loss": 0, "draw": 0}
#         elif player1_goals < player2_goals:
#             return {"win": 0, "loss": 1, "draw": 0}
#         else:
#             return {"win": 0, "loss": 0, "draw": 1}
#     else:
#         if player2_goals > player1_goals:
#             return {"win": 1, "loss": 0, "draw": 0}
#         elif player2_goals < player1_goals:
#             return {"win": 0, "loss": 1, "draw": 0}
#         else:
#             return {"win": 0, "loss": 0, "draw": 1}


# @app.delete("/matches/{match_id}", response_model=dict)
# async def delete_match(match_id: str):
#     match = await db.matches.find_one({"_id": ObjectId(match_id)})
#     if not match:
#         raise HTTPException(status_code=404, detail="Match not found")

#     # Delete match
#     delete_result = await db.matches.delete_one({"_id": ObjectId(match_id)})

#     if delete_result.deleted_count == 0:
#         raise HTTPException(status_code=400, detail="Match deletion failed")

#     return {"message": "Match deleted successfully"}


# @app.post("/tournaments", response_model=Tournament)
# async def create_tournament(tournament: TournamentCreate):
#     tournament_dict = tournament.dict()
#     new_tournament = await db.tournaments.insert_one(tournament_dict)
#     created_tournament = await db.tournaments.find_one({"_id": new_tournament.inserted_id})
#     return {
#         "id": str(created_tournament["_id"]),
#         **{k: v for k, v in created_tournament.items() if k != "_id"}
#     }


# @app.get("/tournaments", response_model=List[Tournament])
# async def get_tournaments():
#     tournaments = await db.tournaments.find().to_list(1000)
#     return [{
#         "id": str(t["_id"]),
#         **{k: v for k, v in t.items() if k != "_id"}
#     } for t in tournaments]


# @app.get("/tournaments/{tournament_id}/matches", response_model=List[Match])
# async def get_tournament_matches(tournament_id: str):
#     matches = await db.matches.find({"tournament_id": tournament_id}).sort("date", -1).to_list(1000)
#     return [Match(**await match_helper(match)) for match in matches]


# @app.get("/")
# async def home():
#     return {"message": "Hello, World!"}

