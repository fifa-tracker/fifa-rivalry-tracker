from fastapi import APIRouter, HTTPException
from bson import ObjectId
from typing import List
from ..schemas.match import Match, MatchCreate, MatchUpdate, HeadToHeadStats
from ..core.database import matches_collection, players_collection
from ..utils.helpers import match_helper, get_result

router = APIRouter()

@router.post("/", response_model=Match)
async def record_match(match: MatchCreate):
    player1 = await players_collection.find_one({"_id": ObjectId(match.player1_id)})
    player2 = await players_collection.find_one({"_id": ObjectId(match.player2_id)})

    if not player1 or not player2:
        raise HTTPException(status_code=404, detail="One or both players not found")

    match_dict = match.dict()
    match_dict["date"] = datetime.now()
    new_match = await matches_collection.insert_one(match_dict)

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
        await players_collection.update_one({"_id": player["_id"]}, update)

    created_match = await matches_collection.find_one({"_id": new_match.inserted_id})
    return Match(**await match_helper(created_match))

@router.get("/", response_model=List[Match])
async def get_matches():
    matches = await matches_collection.find().sort("date", -1).to_list(1000)
    return [Match(**await match_helper(match)) for match in matches]

@router.get("/player/{player_id}", response_model=List[Match])
async def get_player_matches(player_id: str):
    matches = (
        await matches_collection.find(
            {"$or": [{"player1_id": player_id}, {"player2_id": player_id}]}
        )
        .sort("date", -1)
        .to_list(1000)
    )
    return [Match(**await match_helper(match)) for match in matches]

@router.get("/head-to-head/{player1_id}/{player2_id}", response_model=HeadToHeadStats)
async def get_head_to_head_stats(player1_id: str, player2_id: str):
    player1 = await players_collection.find_one({"_id": ObjectId(player1_id)})
    player2 = await players_collection.find_one({"_id": ObjectId(player2_id)})

    if not player1 or not player2:
        raise HTTPException(status_code=404, detail="One or both players not found")

    matches = await matches_collection.find(
        {
            "$or": [
                {"player1_id": player1_id, "player2_id": player2_id},
                {"player1_id": player2_id, "player2_id": player1_id},
            ]
        }
    ).to_list(1000)

    stats = {
        "player1_name": player1["name"],
        "player2_name": player2["name"],
        "total_matches": len(matches),
        "player1_wins": 0,
        "player2_wins": 0,
        "draws": 0,
        "player1_goals": 0,
        "player2_goals": 0,
    }

    for match in matches:
        if match["player1_id"] == player1_id:
            stats["player1_goals"] += match["player1_goals"]
            stats["player2_goals"] += match["player2_goals"]
            if match["player1_goals"] > match["player2_goals"]:
                stats["player1_wins"] += 1
            elif match["player1_goals"] < match["player2_goals"]:
                stats["player2_wins"] += 1
            else:
                stats["draws"] += 1
        else:
            stats["player1_goals"] += match["player2_goals"]
            stats["player2_goals"] += match["player1_goals"]
            if match["player1_goals"] < match["player2_goals"]:
                stats["player1_wins"] += 1
            elif match["player1_goals"] > match["player2_goals"]:
                stats["player2_wins"] += 1
            else:
                stats["draws"] += 1

    # Calculate win rates and average goals
    stats["player1_win_rate"] = (
        stats["player1_wins"] / stats["total_matches"]
        if stats["total_matches"] > 0
        else 0
    )
    stats["player2_win_rate"] = (
        stats["player2_wins"] / stats["total_matches"]
        if stats["total_matches"] > 0
        else 0
    )
    stats["player1_avg_goals"] = (
        stats["player1_goals"] / stats["total_matches"]
        if stats["total_matches"] > 0
        else 0
    )
    stats["player2_avg_goals"] = (
        stats["player2_goals"] / stats["total_matches"]
        if stats["total_matches"] > 0
        else 0
    )

    return HeadToHeadStats(**stats)

@router.put("/{match_id}", response_model=Match)
async def update_match(match_id: str, match_update: MatchUpdate):
    try:
        # Validate match_id format
        if not ObjectId.is_valid(match_id):
            raise HTTPException(status_code=400, detail="Invalid match ID format")

        # Find the match
        match = await matches_collection.find_one({"_id": ObjectId(match_id)})
        
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        # Validate goals are non-negative
        if match_update.player1_goals < 0 or match_update.player2_goals < 0:
            raise HTTPException(status_code=400, detail="Goals cannot be negative")

        # Calculate the changes in goals
        player1_goals_diff = match_update.player1_goals - match["player1_goals"]
        player2_goals_diff = match_update.player2_goals - match["player2_goals"]

        # Check if there are any actual changes
        if player1_goals_diff == 0 and player2_goals_diff == 0:
            # Return the current match data without updating
            return Match(**await match_helper(match))

        # Update match
        update_result = await matches_collection.update_one(
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

            player = await players_collection.find_one({"_id": ObjectId(player_id)})
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

            # Skip player update if there are no changes
            if goals_diff == 0 and opponent_goals_diff == 0 and wins_diff == 0 and losses_diff == 0 and draws_diff == 0:
                continue

            # Update player stats
            await players_collection.update_one(
                {"_id": ObjectId(player_id)},
                {
                    "$inc": {
                        "total_goals_scored": goals_diff,
                        "total_goals_conceded": opponent_goals_diff,
                        "goal_difference": goals_diff - opponent_goals_diff,
                        "wins": wins_diff,
                        "losses": losses_diff,
                        "draws": draws_diff,
                        "points": wins_diff * 3 + draws_diff,
                    }
                },
            )

        # Fetch updated match
        updated_match = await matches_collection.find_one({"_id": ObjectId(match_id)})
        if not updated_match:
            raise HTTPException(status_code=404, detail="Updated match not found")
        
        return Match(**await match_helper(updated_match))

    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid ID format")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{match_id}", response_model=dict)
async def delete_match(match_id: str):
    match = await matches_collection.find_one({"_id": ObjectId(match_id)})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Delete match
    delete_result = await matches_collection.delete_one({"_id": ObjectId(match_id)})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Match deletion failed")

    return {"message": "Match deleted successfully"} 