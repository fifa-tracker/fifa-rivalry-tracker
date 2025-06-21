from typing import List
import logging
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from pydantic import BaseModel

from app.models import TournamentCreate, Tournament, Match
from app.api.dependencies import get_database
from app.utils.helpers import match_helper

logger = logging.getLogger(__name__)

router = APIRouter()

class PlayerIdRequest(BaseModel):
    player_id: str

@router.post("/", response_model=Tournament)
async def create_tournament(tournament: TournamentCreate):
    """Create a new tournament"""
    db = await get_database()
    new_tournament = await db.tournaments.insert_one(tournament.dict())
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
    if player_id not in tournament["player_ids"]:
        raise HTTPException(status_code=404, detail="Player not found in tournament")
    tournament["player_ids"].remove(player_id)
    await db.tournaments.update_one({"_id": ObjectId(tournament_id)}, {"$set": {"player_ids": tournament["player_ids"]}})
    return Tournament(**tournament_helper(tournament))

def tournament_helper(tournament : Tournament):
    return {
        "id": str(tournament["_id"]),
        **{k: v for k, v in tournament.items() if k != "_id"}
    }