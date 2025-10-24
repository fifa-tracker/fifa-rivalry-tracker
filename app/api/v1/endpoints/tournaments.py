from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
import math
import time

from app.models import TournamentCreate, Tournament, Match, User, TournamentPlayerStats, TournamentPlayer, PaginatedResponse, MatchUpdate
from app.models.auth import UserInDB
from app.models.response import success_response, success_list_response, success_paginated_response, StandardResponse, StandardListResponse, StandardPaginatedResponse
from app.api.dependencies import get_database
from app.utils.helpers import match_helper, calculate_tournament_stats, generate_round_robin_matches, generate_missing_matches
from app.utils.auth import get_current_active_user
from app.utils.logging import get_logger
from app.config import settings

logger = get_logger(__name__)

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
    
    # Ensure rounds_per_matchup has a default value for older tournaments
    if "rounds_per_matchup" not in result:
        result["rounds_per_matchup"] = 2
    
    return result

async def get_player_last_5_matches(db, player_id: str, tournament_id: str = None) -> List[str]:
    """Get the last 5 match results for a player as simple characters: W (win), L (loss), D (draw), - (no match)"""
    try:
        # Build query - get matches where player is either player1 or player2
        # Consider matches completed if they have goals scored (regardless of completed field)
        query = {
            "$and": [
                {
                    "$or": [
                        {"player1_id": player_id},
                        {"player2_id": player_id}
                    ]
                },
                {
                    "$or": [
                        {"completed": True},
                        {"player1_goals": {"$exists": True, "$gte": 0}},
                        {"player2_goals": {"$exists": True, "$gte": 0}}
                    ]
                }
            ]
        }
        
        # If tournament_id is provided, filter by tournament
        if tournament_id:
            query["tournament_id"] = tournament_id
        
        # Get matches sorted by date (most recent first)
        matches_cursor = db.matches.find(query).sort("date", -1).limit(5)
        matches = await matches_cursor.to_list(5)
        
        # Convert matches to simple result characters
        results = []
        for match in matches:
            player1_id = match.get("player1_id")
            player2_id = match.get("player2_id")
            player1_goals = match.get("player1_goals", 0)
            player2_goals = match.get("player2_goals", 0)
            
            # Determine match result from current player's perspective
            if player1_id == player_id:
                current_player_goals = player1_goals
                opponent_goals = player2_goals
            else:
                current_player_goals = player2_goals
                opponent_goals = player1_goals
            
            if current_player_goals > opponent_goals:
                results.append("W")  # Win
            elif current_player_goals < opponent_goals:
                results.append("L")  # Loss
            else:
                results.append("D")  # Draw
        
        # Pad with '-' if less than 5 matches
        while len(results) < 5:
            results.append("-")
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting last 5 matches for player {player_id}: {e}")
        return ["-", "-", "-", "-", "-"]  # Return default if error

class PlayerIdRequest(BaseModel):
    player_id: str

class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    rounds_per_matchup: Optional[int] = Field(None, ge=1, description="Number of times each player plays against each other")

@router.post("/", response_model=StandardResponse[Tournament])
async def create_tournament(tournament: TournamentCreate, current_user: UserInDB = Depends(get_current_active_user)):
    """Create a new tournament with automatic round-robin match generation"""
    db = await get_database()
    
    # Validate that all player IDs exist
    if tournament.player_ids:
        try:
            player_object_ids = [ObjectId(pid) for pid in tournament.player_ids]
            existing_players = await db.users.find({"_id": {"$in": player_object_ids}}).to_list(len(tournament.player_ids))
            
            if len(existing_players) != len(tournament.player_ids):
                raise HTTPException(status_code=400, detail="One or more player IDs are invalid")
                
        except Exception as e:
            logger.error(f"Error validating player IDs: {e}")
            raise HTTPException(status_code=400, detail="Invalid player ID format")
    
    # Convert to dict with default values
    tournament_dict = tournament.model_dump()
    tournament_dict["matches"] = []
    tournament_dict["matches_count"] = 0
    tournament_dict["completed"] = False
    tournament_dict["owner_id"] = str(current_user.id)
    
    # Create the tournament first
    new_tournament = await db.tournaments.insert_one(tournament_dict)
    tournament_id = str(new_tournament.inserted_id)
    
    # Generate and insert round-robin matches if there are players
    if tournament.player_ids and len(tournament.player_ids) >= 2:
        matches = generate_round_robin_matches(
            tournament.player_ids, 
            tournament_id, 
            tournament.rounds_per_matchup
        )
        
        if matches:
            # Insert all matches
            inserted_matches = await db.matches.insert_many(matches)
            match_ids = [str(match_id) for match_id in inserted_matches.inserted_ids]
            
            # Update tournament with match IDs and count
            await db.tournaments.update_one(
                {"_id": new_tournament.inserted_id},
                {
                    "$set": {
                        "matches": match_ids,
                        "matches_count": len(match_ids)
                    }
                }
            )
            
            logger.info(f"Created tournament {tournament_id} with {len(matches)} auto-generated matches")
    
    # Get the final tournament with all data
    created_tournament = await db.tournaments.find_one({"_id": new_tournament.inserted_id})
    return success_response(
        data=Tournament(**tournament_helper(created_tournament)),
        message="Tournament created successfully"
    )

@router.get("/", response_model=StandardListResponse[Tournament])
async def get_tournaments(current_user: UserInDB = Depends(get_current_active_user)):
    """Get tournaments that the current user is part of"""
    db = await get_database()
    current_user_id = str(current_user.id)
    
    # Find tournaments where the current user is either:
    # 1. The owner of the tournament, OR
    # 2. A participant in the tournament (their ID is in player_ids)
    tournaments = await db.tournaments.find({
        "$or": [
            {"owner_id": current_user_id},
            {"player_ids": current_user_id}
        ]
    }).to_list(1000)
    
    processed_tournaments = [Tournament(**tournament_helper(t)) for t in tournaments]
    return success_list_response(
        items=processed_tournaments,
        message=f"Retrieved {len(processed_tournaments)} tournaments"
    )

@router.get("/{tournament_id}/matches", response_model=StandardPaginatedResponse[Match])
async def get_tournament_matches(
    tournament_id: str, 
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="Number of items per page"),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all matches for a specific tournament with pagination"""
    start_time = time.time()
    logger.info(f"Starting tournament matches request - tournament_id: {tournament_id}, page: {page}, page_size: {page_size}")
    
    db = await get_database()
    db_time = time.time()
    logger.info(f"Database connection established in {(db_time - start_time) * 1000:.2f}ms")
    
    # Validate tournament exists
    tournament_start = time.time()
    tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    tournament_time = time.time()
    logger.info(f"Tournament validation query completed in {(tournament_time - tournament_start) * 1000:.2f}ms")
    
    if not tournament:
        logger.warning(f"Tournament not found - tournament_id: {tournament_id}")
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Calculate skip value for pagination
    skip = (page - 1) * page_size
    
    # Get total count of matches for this tournament
    count_start = time.time()
    total_matches = await db.matches.count_documents({"tournament_id": tournament_id})
    count_time = time.time()
    logger.info(f"Match count query completed in {(count_time - count_start) * 1000:.2f}ms - total_matches: {total_matches}")
    
    # Get paginated matches
    matches_start = time.time()
    matches_cursor = db.matches.find({"tournament_id": tournament_id}).sort("date", -1).skip(skip).limit(page_size)
    matches = await matches_cursor.to_list(page_size)
    matches_time = time.time()
    logger.info(f"Matches fetch query completed in {(matches_time - matches_start) * 1000:.2f}ms - fetched_matches: {len(matches)}")
    
    # Fetch all unique player IDs from the matches
    player_ids_start = time.time()
    unique_player_ids = set()
    for match in matches:
        if match.get("player1_id"):
            unique_player_ids.add(match["player1_id"])
        if match.get("player2_id"):
            unique_player_ids.add(match["player2_id"])
    
    # Fetch all players in one query
    players = {}
    if unique_player_ids:
        player_objects = await db.users.find({"_id": {"$in": [ObjectId(pid) for pid in unique_player_ids]}}).to_list(len(unique_player_ids))
        players = {str(player["_id"]): player for player in player_objects}
    
    player_ids_time = time.time()
    logger.info(f"Player data fetch completed in {(player_ids_time - player_ids_start) * 1000:.2f}ms - unique_players: {len(players)}")
    
    # Process matches with helper function using pre-fetched data
    processing_start = time.time()
    processed_matches = []
    for match in matches:
        # Create a simplified match_helper that uses pre-fetched data
        match_id = str(match.get("_id", "unknown"))
        
        # Get player information from pre-fetched data
        player1_id = match.get("player1_id")
        player2_id = match.get("player2_id")
        
        if not player1_id or not player2_id:
            player1_name = "Unknown Player"
            player2_name = "Unknown Player"
        else:
            player1 = players.get(player1_id)
            player2 = players.get(player2_id)
            
            # Handle deleted players
            if player1 and player1.get("is_deleted", False):
                player1_name = "Deleted Player"
            else:
                player1_name = player1["username"] if player1 else "Unknown Player"
                
            if player2 and player2.get("is_deleted", False):
                player2_name = "Deleted Player"
            else:
                player2_name = player2["username"] if player2 else "Unknown Player"
        
        processed_match = {
            "id": str(match["_id"]),
            "player1_name": player1_name,
            "player2_name": player2_name,
            "player1_goals": match.get("player1_goals", 0),
            "player2_goals": match.get("player2_goals", 0),
            "date": match.get("date", datetime.now()),
            "team1": match.get("team1", "Unknown"),
            "team2": match.get("team2", "Unknown"),
            "half_length": match.get("half_length", 4),
            "completed": match.get("completed", False),  # Include completed status
            "tournament_name": tournament["name"] if tournament else None
        }
        
        processed_matches.append(Match(**processed_match))
    
    processing_time = time.time()
    logger.info(f"Match processing completed in {(processing_time - processing_start) * 1000:.2f}ms - processed_matches: {len(processed_matches)}")
    
    # Calculate pagination metadata
    total_pages = math.ceil(total_matches / page_size) if total_matches > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1
    
    total_time = time.time()
    logger.info(f"Tournament matches request completed in {(total_time - start_time) * 1000:.2f}ms - tournament_id: {tournament_id}, page: {page}, total_matches: {total_matches}, returned_matches: {len(processed_matches)}")
    
    return success_paginated_response(
        items=processed_matches,
        total=total_matches,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
        message=f"Retrieved {len(processed_matches)} matches (page {page} of {total_pages})"
    )

@router.get("/{tournament_id}/", response_model=StandardResponse[Tournament])
async def get_tournament(tournament_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get a specific tournament"""
    db = await get_database()
    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return success_response(
        data=Tournament(**tournament_helper(tournament)),
        message="Tournament retrieved successfully"
    )

@router.put("/{tournament_id}/", response_model=Tournament)
async def update_tournament(tournament_id: str, tournament_update: TournamentUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    """Update tournament details"""
    db = await get_database()
    
    # Check if tournament exists
    tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Get only the fields that are provided in the update request
    update_data = tournament_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Validate date logic if both dates are provided
    if update_data.get("start_date") and update_data.get("end_date"):
        if update_data["start_date"] > update_data["end_date"]:
            raise HTTPException(status_code=400, detail="Start date cannot be after end date")
    
    # Check if rounds_per_matchup is being updated and tournament has players
    regenerate_matches = False
    if "rounds_per_matchup" in update_data and tournament.get("player_ids") and len(tournament["player_ids"]) >= 2:
        if not tournament.get("completed", False):
            regenerate_matches = True
        else:
            raise HTTPException(status_code=400, detail="Cannot change rounds per matchup for a completed tournament")
    
    # Update the tournament
    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)}, 
        {"$set": update_data}
    )
    
    # Regenerate matches if rounds_per_matchup was changed
    # !!!!!!! Rework this, already existing matches should be kept
    if regenerate_matches:
        # Delete all existing matches for this tournament
        if tournament.get("matches"):
            await db.matches.delete_many({"tournament_id": tournament_id})
            logger.info(f"Deleted existing matches for tournament {tournament_id}")
        
        # Generate new round-robin matches
        new_rounds_per_matchup = update_data.get("rounds_per_matchup", tournament.get("rounds_per_matchup", 2))
        new_matches = generate_round_robin_matches(
            tournament["player_ids"], 
            tournament_id, 
            new_rounds_per_matchup
        )
        
        match_ids = []
        if new_matches:
            # Insert all new matches
            inserted_matches = await db.matches.insert_many(new_matches)
            match_ids = [str(match_id) for match_id in inserted_matches.inserted_ids]
            logger.info(f"Generated {len(new_matches)} new matches for tournament {tournament_id}")
        
        # Update tournament with new matches
        await db.tournaments.update_one(
            {"_id": ObjectId(tournament_id)}, 
            {
                "$set": {
                    "matches": match_ids,
                    "matches_count": len(match_ids)
                }
            }
        )
    
    # Return the updated tournament
    updated_tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    return Tournament(**tournament_helper(updated_tournament))

@router.delete("/{tournament_id}/", response_model=StandardResponse[dict])
async def delete_tournament(tournament_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Delete a tournament and all its associated matches"""
    db = await get_database()
    
    # Check if tournament exists
    tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Validate that the current user is the owner of the tournament
    tournament_owner_id = tournament.get("owner_id")
    current_user_id = str(current_user.id)
    
    if tournament_owner_id != current_user_id:
        raise HTTPException(
            status_code=403, 
            detail="You can only delete tournaments that you created"
        )
    
    # Delete all matches associated with this tournament
    matches_deleted = await db.matches.delete_many({"tournament_id": tournament_id})
    logger.info(f"Deleted {matches_deleted.deleted_count} matches for tournament {tournament_id}")
    
    # Delete the tournament
    await db.tournaments.delete_one({"_id": ObjectId(tournament_id)})
    logger.info(f"Deleted tournament {tournament_id} by user {current_user_id}")
    
    return success_response(
        data={"message": "Tournament and all associated matches deleted successfully"},
        message="Tournament and all associated matches deleted successfully"
    )

@router.post("/{tournament_id}/players", response_model=Tournament)
async def add_player_to_tournament(tournament_id: str, player_request: PlayerIdRequest, current_user: UserInDB = Depends(get_current_active_user)):
    """Add a player to a tournament and generate missing matches while preserving completed ones"""
    db = await get_database()
    logger.info(f"Adding player {player_request.player_id} to tournament {tournament_id}")
    
    # Validate tournament exists
    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Check if tournament is completed
    if tournament.get("completed", False):
        raise HTTPException(status_code=400, detail="Cannot add players to a completed tournament")
    
    # Validate player exists
    try:
        player = await db.users.find_one({"_id": ObjectId(player_request.player_id)})
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid player ID format")
    
    # Initialize player_ids if it doesn't exist
    if "player_ids" not in tournament:
        tournament["player_ids"] = []
    
    # Check if player is already in tournament (convert to string for comparison)
    player_id_str = str(player_request.player_id)
    if player_id_str in [str(pid) for pid in tournament["player_ids"]]:
        raise HTTPException(status_code=400, detail="Player already in tournament")
    
    # Add player ID to tournament
    tournament["player_ids"].append(player_id_str)
    
    # Get existing matches for this tournament
    existing_matches = await db.matches.find({"tournament_id": tournament_id}).to_list(1000)
    
    # Generate only the missing matches to complete the round-robin format
    new_matches = []
    match_ids = []
    
    if len(tournament["player_ids"]) >= 2:
        from app.utils.helpers import generate_missing_matches
        rounds_per_matchup = tournament.get("rounds_per_matchup", 2)
        new_matches = generate_missing_matches(
            existing_matches,
            tournament["player_ids"], 
            tournament_id, 
            rounds_per_matchup
        )
        
        if new_matches:
            # Insert only the new matches
            inserted_matches = await db.matches.insert_many(new_matches)
            new_match_ids = [str(match_id) for match_id in inserted_matches.inserted_ids]
            
            # Combine existing match IDs with new ones
            existing_match_ids = [str(match["_id"]) for match in existing_matches]
            match_ids = existing_match_ids + new_match_ids
            
            logger.info(f"Generated {len(new_matches)} new matches for tournament {tournament_id}. Total matches: {len(match_ids)}")
        else:
            # No new matches needed, just keep existing ones
            match_ids = [str(match["_id"]) for match in existing_matches]
            logger.info(f"No new matches needed for tournament {tournament_id}. Keeping {len(match_ids)} existing matches.")
    
    # Update tournament with new player and updated match list
    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)}, 
        {
            "$set": {
                "player_ids": tournament["player_ids"],
                "matches": match_ids,
                "matches_count": len(match_ids)
            }
        }
    )
    
    # Get updated tournament
    updated_tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    return Tournament(**tournament_helper(updated_tournament))

@router.get("/{tournament_id}/players", response_model=List[TournamentPlayer])
async def get_tournament_players(tournament_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get all players in a tournament"""
    db = await get_database()
    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Handle player_ids - they might be stored as strings or ObjectIds
    player_ids = tournament.get("player_ids", [])
    
    if not player_ids:
        return []
    
    # Convert string IDs to ObjectIds for database query
    try:
        player_object_ids = [ObjectId(pid) if isinstance(pid, str) else pid for pid in player_ids]
        players = await db.users.find({"_id": {"$in": player_object_ids}}).to_list(1000)
        
        # Convert to TournamentPlayer objects with proper ID conversion (excluding email)
        result = []
        for player in players:
            player_dict = {
                "id": str(player["_id"]),
                **{k: v for k, v in player.items() if k != "_id" and k != "email"}
            }
            result.append(TournamentPlayer(**player_dict))
        
        return result
    except Exception as e:
        logger.error(f"Error fetching tournament players: {e}")
        raise HTTPException(status_code=500, detail="Error fetching tournament players")

@router.delete("/{tournament_id}/players/{player_id}", response_model=Tournament)
async def remove_player_from_tournament(tournament_id: str, player_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Remove a player from a tournament and regenerate matches while preserving completed ones"""
    db = await get_database()
    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Check if tournament is completed
    if tournament.get("completed", False):
        raise HTTPException(status_code=400, detail="Cannot remove players from a completed tournament")
    
    # Initialize player_ids if it doesn't exist
    if "player_ids" not in tournament:
        tournament["player_ids"] = []
    
    # Check if player is in tournament (convert to string for comparison)
    player_id_str = str(player_id)
    if player_id_str not in [str(pid) for pid in tournament["player_ids"]]:
        raise HTTPException(status_code=404, detail="Player not found in tournament")
    
    # Remove player ID
    tournament["player_ids"] = [str(pid) for pid in tournament["player_ids"] if str(pid) != player_id_str]
    
    # Get all existing matches for this tournament
    all_existing_matches = await db.matches.find({"tournament_id": tournament_id}).to_list(1000)
    
    # Separate matches into those that involve the removed player and those that don't
    matches_to_keep = []
    matches_to_remove = []
    
    for match in all_existing_matches:
        match_player1_id = str(match.get("player1_id", ""))
        match_player2_id = str(match.get("player2_id", ""))
        
        # If the match involves the removed player, mark it for removal
        if player_id_str in [match_player1_id, match_player2_id]:
            matches_to_remove.append(match)
        else:
            # Keep matches that don't involve the removed player and where both players are still in tournament
            if match_player1_id in tournament["player_ids"] and match_player2_id in tournament["player_ids"]:
                matches_to_keep.append(match)
    
    # Delete only the matches that involve the removed player
    if matches_to_remove:
        match_ids_to_remove = [match["_id"] for match in matches_to_remove]
        await db.matches.delete_many({"_id": {"$in": match_ids_to_remove}})
        logger.info(f"Deleted {len(matches_to_remove)} matches involving removed player {player_id_str} from tournament {tournament_id}")
    
    # Generate missing matches for the remaining players (if needed)
    new_matches = []
    match_ids = []
    
    if len(tournament["player_ids"]) >= 2:
        from app.utils.helpers import generate_missing_matches
        rounds_per_matchup = tournament.get("rounds_per_matchup", 2)
        new_matches = generate_missing_matches(
            matches_to_keep,
            tournament["player_ids"], 
            tournament_id, 
            rounds_per_matchup
        )
        
        if new_matches:
            # Insert the new matches
            inserted_matches = await db.matches.insert_many(new_matches)
            new_match_ids = [str(match_id) for match_id in inserted_matches.inserted_ids]
            
            # Combine kept matches with new ones
            kept_match_ids = [str(match["_id"]) for match in matches_to_keep]
            match_ids = kept_match_ids + new_match_ids
            
            logger.info(f"Generated {len(new_matches)} new matches after removing player {player_id_str}. Total matches: {len(match_ids)}")
        else:
            # No new matches needed, just keep existing valid ones
            match_ids = [str(match["_id"]) for match in matches_to_keep]
            logger.info(f"No new matches needed after removing player {player_id_str}. Keeping {len(match_ids)} existing matches.")
    else:
        # Less than 2 players remaining, no matches possible
        match_ids = []
        logger.info(f"Less than 2 players remaining in tournament {tournament_id} after removing player {player_id_str}")
    
    # Update tournament with remaining players and updated matches
    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)}, 
        {
            "$set": {
                "player_ids": tournament["player_ids"],
                "matches": match_ids,
                "matches_count": len(match_ids)
            }
        }
    )
    
    # Get updated tournament
    updated_tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    return Tournament(**tournament_helper(updated_tournament))

@router.get("/{tournament_id}/stats", response_model=List[TournamentPlayerStats])
async def get_tournament_stats(tournament_id: str, current_user: UserInDB = Depends(get_current_active_user)):
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
        players : List[User] = await db.users.find({"_id": {"$in": player_object_ids}}).to_list(1000)
        logger.info(f"Found {len(players)} players in database")
    except Exception as e:
        logger.error(f"Error converting player IDs: {e}")
        return []
    
    # Check if tournament has rounds_per_matchup field to determine if we should filter by completion
    if "rounds_per_matchup" in tournament:
        # New tournament format - only count completed matches
        matches : List[Match] = await db.matches.find({"tournament_id": tournament_id, "completed": True}).to_list(1000)
        logger.info(f"Found {len(matches)} completed matches for tournament (filtering by completion)")
        no_matches_message = "No completed matches found for tournament, returning empty stats"
    else:
        # Legacy tournament format - count all matches
        matches : List[Match] = await db.matches.find({"tournament_id": tournament_id}).to_list(1000)
        logger.info(f"Found {len(matches)} matches for tournament (legacy format - no completion filter)")
        no_matches_message = "No matches found for tournament, returning empty stats"
    
    if not players:
        logger.warning("No players found in database")
        return []
    
    if not matches:
        logger.info(no_matches_message)
        # Return players with zero stats
        tournament_stats = []
        for player in players:
            # Get last 5 matches for this player (not filtered by tournament)
            last_5_matches = await get_player_last_5_matches(db, str(player["_id"]))
            
            player_stats = TournamentPlayerStats(
                id=str(player["_id"]),
                username=player["username"],
                first_name=player.get("first_name"),
                last_name=player.get("last_name"),
                total_matches=0,
                total_goals_scored=0,
                total_goals_conceded=0,
                goal_difference=0,
                wins=0,
                losses=0,
                draws=0,
                points=0,
                last_5_matches=last_5_matches
            )
            tournament_stats.append(player_stats)
        return tournament_stats

    # Calculate tournament statistics for each player
    tournament_stats = []
    for player in players:
        player_id = str(player["_id"])
        logger.info(f"Calculating stats for player {player['username']} (ID: {player_id})")
        stats = calculate_tournament_stats(player_id, matches)
        
        # Get last 5 matches for this player (filtered by tournament)
        last_5_matches = await get_player_last_5_matches(db, player_id, tournament_id)
        
        # Create player stats object with tournament-specific data
        player_stats = TournamentPlayerStats(
            id=player_id,
            username=player["username"],
            first_name=player.get("first_name"),
            last_name=player.get("last_name"),
            total_matches=stats["total_matches"],
            total_goals_scored=stats["total_goals_scored"],
            total_goals_conceded=stats["total_goals_conceded"],
            goal_difference=stats["goal_difference"],
            wins=stats["wins"],
            losses=stats["losses"],
            draws=stats["draws"],
            points=stats["points"],
            last_5_matches=last_5_matches
        )
        
        tournament_stats.append(player_stats)
        logger.info(f"Player {player['username']} tournament stats: {stats}")

    # Sort by points (descending), then goal difference (descending), then goals scored (descending)
    tournament_stats.sort(key=lambda x: (x.points, x.goal_difference, x.total_goals_scored), reverse=True)
    
    return tournament_stats

@router.post("/tournament/{tournament_id}/match", response_model=Tournament)
async def add_match_to_tournament(tournament_id: str, match: Match, current_user: UserInDB = Depends(get_current_active_user)):
    """Add a match to a tournament"""
    db = await get_database()
    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    await db.matches.insert_one(match.model_dump())
    await db.tournaments.update_one({"_id": ObjectId(tournament_id)}, {"$set": {"matches_count": tournament["matches_count"] + 1}})
    tournament["matches_count"] = tournament["matches_count"] + 1
    return Tournament(**tournament_helper(tournament))

@router.delete("/tournament/{tournament_id}/match/{match_id}", response_model=dict)
async def delete_match_from_tournament(tournament_id: str, match_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Delete a match from a tournament"""
    db = await get_database()
    
    # Check if tournament exists
    tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Validate that the current user is the owner of the tournament
    tournament_owner_id = tournament.get("owner_id")
    current_user_id = str(current_user.id)
    
    if tournament_owner_id != current_user_id:
        raise HTTPException(
            status_code=403, 
            detail="You can only delete matches from tournaments that you created"
        )
    
    # Check if match exists and belongs to this tournament
    try:
        match = await db.matches.find_one({"_id": ObjectId(match_id), "tournament_id": tournament_id})
        if not match:
            raise HTTPException(status_code=404, detail="Match not found in this tournament")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid match ID format")
    
    # Delete the match
    await db.matches.delete_one({"_id": ObjectId(match_id)})
    logger.info(f"Deleted match {match_id} from tournament {tournament_id} by user {current_user_id}")
    
    # Update tournament matches count
    current_matches_count = tournament.get("matches_count", 0)
    new_matches_count = max(0, current_matches_count - 1)  # Ensure count doesn't go below 0
    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)}, 
        {"$set": {"matches_count": new_matches_count}}
    )
    
    return {"message": "Match deleted successfully from tournament"}

@router.put("/tournament/{tournament_id}/match/{match_id}", response_model=Match)
async def edit_match_in_tournament(
    tournament_id: str, 
    match_id: str, 
    match_update: MatchUpdate, 
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Edit a match in a tournament"""
    db = await get_database()
    
    # Check if tournament exists
    tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Validate that the current user is the owner of the tournament
    tournament_owner_id = tournament.get("owner_id")
    current_user_id = str(current_user.id)
    
    if tournament_owner_id != current_user_id:
        raise HTTPException(
            status_code=403, 
            detail="You can only edit matches in tournaments that you created"
        )
    
    # Check if match exists and belongs to this tournament
    try:
        match = await db.matches.find_one({"_id": ObjectId(match_id), "tournament_id": tournament_id})
        if not match:
            raise HTTPException(status_code=404, detail="Match not found in this tournament")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid match ID format")
    
    # Get only the fields that are provided in the update request
    update_data = match_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update the match
    await db.matches.update_one(
        {"_id": ObjectId(match_id)}, 
        {"$set": update_data}
    )
    
    # Return the updated match
    updated_match = await db.matches.find_one({"_id": ObjectId(match_id)})
    return Match(**await match_helper(updated_match, db))

@router.post("/{tournament_id}/end", response_model=Tournament)
async def end_tournament(tournament_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """End a tournament by marking it as completed and setting the end date"""
    db = await get_database()
    
    # Check if tournament exists
    tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Validate that the current user is the owner of the tournament
    tournament_owner_id = tournament.get("owner_id")
    current_user_id = str(current_user.id)
    
    if tournament_owner_id != current_user_id:
        raise HTTPException(
            status_code=403, 
            detail="You can only end tournaments that you created"
        )
    
    # Check if tournament is already completed
    if tournament.get("completed", False):
        raise HTTPException(
            status_code=400, 
            detail="Tournament is already completed"
        )
    
    # Get all players in the tournament
    player_ids = tournament.get("player_ids", [])
    logger.info(f"Ending tournament {tournament_id} with {len(player_ids)} players")
    
    # Update tournament to mark it as completed and set end date
    current_time = datetime.now()
    update_data = {
        "completed": True,
        "end_date": current_time
    }
    
    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)}, 
        {"$set": update_data}
    )
    
    # Increment tournaments_played count for all players in the tournament
    if player_ids:
        try:
            # Convert string IDs to ObjectIds for database query
            player_object_ids = [ObjectId(pid) if isinstance(pid, str) else pid for pid in player_ids]
            
            # Update all players' tournaments_played count
            result = await db.users.update_many(
                {"_id": {"$in": player_object_ids}},
                {"$inc": {"tournaments_played": 1}}
            )
            
            logger.info(f"Updated tournaments_played count for {result.modified_count} players in tournament {tournament_id}")
            
        except Exception as e:
            logger.error(f"Error updating player tournament counts: {e}")
            # Don't fail the entire operation if player count update fails
            # The tournament is still marked as completed
    
    # Return the updated tournament
    updated_tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    logger.info(f"Tournament {tournament_id} ended by user {current_user_id} at {current_time}")
    
    return Tournament(**tournament_helper(updated_tournament))