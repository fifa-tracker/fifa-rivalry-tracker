from typing import List, Union
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from app.models import Player, HeadToHeadStats, RecentMatch, UserStatsWithMatches
from app.models.auth import UserInDB
from app.models.response import success_response, StandardResponse
from app.api.dependencies import get_database

from app.utils.auth import user_helper
from app.utils.auth import get_current_active_user
from app.utils.helpers import calculate_head_to_head_stats

router = APIRouter()

@router.get("/", response_model=StandardResponse[UserStatsWithMatches])
async def get_stats(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current user's stats along with their last 5 matches"""
    db = await get_database()
    
    # Get user's last 5 matches
    user_matches = await db.matches.find({
        "$or": [
            {"player1_id": str(current_user.id)},
            {"player2_id": str(current_user.id)}
        ]
    }).sort("date", -1).limit(5).to_list(5)
    
    # Convert matches to RecentMatch format
    recent_matches = []
    for match in user_matches:
        # Get tournament name if available
        tournament_name = None
        if match.get("tournament_id"):
            tournament = await db.tournaments.find_one({"_id": ObjectId(match["tournament_id"])})
            if tournament:
                tournament_name = tournament.get("name")
        
        # Get opponent information
        opponent_id = match["player2_id"] if match["player1_id"] == str(current_user.id) else match["player1_id"]
        opponent = await db.users.find_one({"_id": ObjectId(opponent_id)})
        
        # Determine current player's goals and opponent's goals
        current_player_goals = match["player1_goals"] if match["player1_id"] == str(current_user.id) else match["player2_goals"]
        opponent_goals = match["player2_goals"] if match["player1_id"] == str(current_user.id) else match["player1_goals"]
        
        # Determine match result from current player's perspective
        if current_player_goals > opponent_goals:
            match_result = "win"
        elif current_player_goals < opponent_goals:
            match_result = "loss"
        else:
            match_result = "draw"
        
        recent_match = RecentMatch(
            date=match["date"],
            player1_goals=match["player1_goals"],
            player2_goals=match["player2_goals"],
            tournament_name=tournament_name,
            team1=match.get("team1"),
            team2=match.get("team2"),
            opponent_id=opponent_id,
            opponent_username=opponent.get("username") if opponent else None,
            opponent_first_name=opponent.get("first_name") if opponent else None,
            opponent_last_name=opponent.get("last_name") if opponent else None,
            current_player_id=str(current_user.id),
            current_player_username=current_user.username,
            current_player_goals=current_player_goals,
            opponent_goals=opponent_goals,
            match_result=match_result
        )
        recent_matches.append(recent_match)
    
    # Create UserStatsWithMatches response
    user_stats = UserStatsWithMatches(
        id=str(current_user.id),
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        total_matches=current_user.total_matches,
        total_goals_scored=current_user.total_goals_scored,
        total_goals_conceded=current_user.total_goals_conceded,
        goal_difference=current_user.goal_difference,
        wins=current_user.wins,
        losses=current_user.losses,
        draws=current_user.draws,
        points=current_user.points,
        elo_rating=current_user.elo_rating,
        tournaments_played=current_user.tournaments_played,
        last_5_teams=current_user.last_5_teams,
        last_5_matches=recent_matches
    )
    
    return success_response(
        data=user_stats,
        message="User statistics retrieved successfully"
    )

@router.get("/head-to-head/{player1_id}/{player2_id}", response_model=StandardResponse[HeadToHeadStats])
async def get_head_to_head_stats(player1_id: str, player2_id: str):
    """Get head-to-head statistics between two players"""
    db = await get_database()
    player1 = await db.users.find_one({"_id": ObjectId(player1_id)})
    player2 = await db.users.find_one({"_id": ObjectId(player2_id)})

    if not player1 or not player2:
        raise HTTPException(status_code=404, detail="One or both players not found")

    # Calculate head-to-head stats
    head_to_head_stats = await calculate_head_to_head_stats(db, player1_id, player2_id, player1, player2)
    return success_response(
        data=head_to_head_stats,
        message="Head-to-head statistics retrieved successfully"
    )
