from typing import List
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime

from app.models import MatchCreate, Match, MatchUpdate, Player, Tournament
from app.models.auth import UserInDB
from app.api.dependencies import get_database
from app.utils.helpers import match_helper, get_result
from app.utils.auth import get_current_active_user
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post("/", response_model=Match)
async def record_match(match: MatchCreate, current_user: UserInDB = Depends(get_current_active_user)):
    """Record a new match"""
    db = await get_database()
    player1 : Player = await db.users.find_one({"_id": ObjectId(match.player1_id)})
    player2 : Player = await db.users.find_one({"_id": ObjectId(match.player2_id)})

    if not player1 or not player2:
        raise HTTPException(status_code=404, detail="One or both players not found")
    
    match_dict = match.model_dump()
    match_dict["date"] = datetime.now()
    new_match = await db.matches.insert_one(match_dict)

    tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(match.tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Initialize matches field if it doesn't exist (for backward compatibility)
    if "matches" not in tournament:
        tournament["matches"] = []
    if "matches_count" not in tournament:
        tournament["matches_count"] = 0

    tournament["matches"].append(new_match.inserted_id)
    await db.tournaments.update_one({"_id": ObjectId(match.tournament_id)}, {"$set": {"matches": tournament["matches"], "matches_count": tournament["matches_count"] + 1}})

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
                "goal_difference" : goals_scored - goals_conceded,
                "wins": 1 if goals_scored > goals_conceded else 0,
                "losses": 1 if goals_scored < goals_conceded else 0,
                "draws": 1 if goals_scored == goals_conceded else 0,
                "points": (
                    3
                    if goals_scored > goals_conceded
                    else (1 if goals_scored == goals_conceded else 0)
                ),
            }
        }
        await db.users.update_one({"_id": player["_id"]}, update)

    created_match = await db.matches.find_one({"_id": new_match.inserted_id})
    return Match(**await match_helper(created_match, db))

@router.get("/", response_model=List[Match])
async def get_matches(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all matches"""
    db = await get_database()
    matches = await db.matches.find().sort("date", -1).to_list(1000)
    logger.debug(f"Retrieved {len(matches)} matches")
    return [Match(**await match_helper(match, db)) for match in matches]

@router.put("/{match_id}", response_model=Match)
async def update_match(match_id: str, match_update: MatchUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    """Update a match"""
    try:
        db = await get_database()
        match : Match = await db.matches.find_one({"_id": ObjectId(match_id)})
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        # Validate goals are non-negative
        if match_update.player1_goals < 0 or match_update.player2_goals < 0:
            raise HTTPException(status_code=400, detail="Goals cannot be negative")
        
        player1_goals_diff  = match_update.player1_goals - match["player1_goals"]
        player2_goals_diff = match_update.player2_goals - match["player2_goals"]
        
        # Check if there are any actual changes
        if player1_goals_diff == 0 and player2_goals_diff == 0:
            return Match(**await match_helper(match, db))
        
        # Update match
        update_result = await db.matches.update_one(
            {"_id": ObjectId(match_id)},
            {
                "$set": {
                    "player1_goals": match_update.player1_goals,
                    "player2_goals": match_update.player2_goals,
                }
            },
        )
        
        if update_result.matched_count == 0:
            raise HTTPException(status_code=400, detail="Match update failed - match not found")
        
        # Update player stats
        for player_id, goals_diff, opponent_goals_diff in [
            (match["player1_id"], player1_goals_diff, player2_goals_diff),
            (match["player2_id"], player2_goals_diff, player1_goals_diff),
        ]:
            if not ObjectId.is_valid(player_id):
                continue
            
            player : Player = await db.users.find_one({"_id": ObjectId(player_id)})
            if not player:
                continue
            
            # Calculate win/loss/draw changes
            old_result = get_result(
                match["player1_goals"],
                match["player2_goals"],
                player_id == match["player1_id"],
            )
            new_result = get_result(
                match_update.player1_goals,
                match_update.player2_goals,
                player_id == match["player1_id"],
            )
            wins_diff = new_result["win"] - old_result["win"]
            losses_diff = new_result["loss"] - old_result["loss"]
            draws_diff = new_result["draw"] - old_result["draw"]

            if goals_diff == 0 and opponent_goals_diff == 0 and wins_diff == 0 and losses_diff == 0 and draws_diff == 0:
                continue
            
            update = {
                "$inc": {
                    "total_matches": 1,
                    "total_goals_scored": goals_diff,
                    "total_goals_conceded": opponent_goals_diff,
                    "goal_difference" : goals_diff - opponent_goals_diff,
                    "wins": wins_diff,
                    "losses": losses_diff,
                    "draws": draws_diff,
                    "points": (
                        3
                        if goals_diff > opponent_goals_diff
                        else (1 if goals_diff == opponent_goals_diff else 0)
                    ),
                }
            }
            update_result = await db.users.update_one({"_id": player["_id"]}, update)
            if update_result.modified_count == 0:
                raise HTTPException(status_code=400, detail="Player update failed")

        # Fetch updated match
        updated_match = await db.matches.find_one({"_id": ObjectId(match_id)})
        if not updated_match:
            raise HTTPException(status_code=404, detail="Updated match not found")

        return Match(**await match_helper(updated_match, db))

    except Exception as e:
        logger.error(f"Error updating match: {str(e)}")
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid ID format")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{match_id}", response_model=dict)
async def delete_match(match_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Delete a match"""
    db = await get_database()
    match : Match = await db.matches.find_one({"_id": ObjectId(match_id)})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    delete_result = await db.matches.delete_one({"_id": ObjectId(match_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Match deletion failed")

    return {"message": "Match deleted successfully"}