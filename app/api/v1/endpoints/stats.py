from typing import List
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from app.models import Player, HeadToHeadStats
from app.models.auth import UserInDB
from app.api.dependencies import get_database

from app.utils.auth import user_helper
from app.utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[Player])
async def get_stats(current_user: UserInDB = Depends(get_current_active_user)):
    """Get player stats/leaderboard (excluding deleted players)"""
    db = await get_database()
    players = await db.users.find({"is_deleted": {"$ne": True}}).sort([("points", -1), ("goal_difference", -1)]).to_list(1000)
    return [user_helper(player) for player in players]

@router.get("/head-to-head/{player1_id}/{player2_id}", response_model=HeadToHeadStats)
async def get_head_to_head_stats(player1_id: str, player2_id: str):
    """Get head-to-head statistics between two players"""
    db = await get_database()
    player1 = await db.users.find_one({"_id": ObjectId(player1_id)})
    player2 = await db.users.find_one({"_id": ObjectId(player2_id)})

    if not player1 or not player2:
        raise HTTPException(status_code=404, detail="One or both players not found")

    # Add your head-to-head calculation logic here from main.py
    pass
