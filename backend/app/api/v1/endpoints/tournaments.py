from typing import List
from fastapi import APIRouter
from bson import ObjectId

from app.models import TournamentCreate, Tournament, Match
from app.api.dependencies import get_database
from app.utils.helpers import match_helper

router = APIRouter()

@router.post("/", response_model=Tournament)
async def create_tournament(tournament: TournamentCreate):
    """Create a new tournament"""
    db = await get_database()
    tournament_dict = tournament.dict()
    new_tournament = await db.tournaments.insert_one(tournament_dict)
    created_tournament = await db.tournaments.find_one({"_id": new_tournament.inserted_id})
    return {
        "id": str(created_tournament["_id"]),
        **{k: v for k, v in created_tournament.items() if k != "_id"}
    }

@router.get("/", response_model=List[Tournament])
async def get_tournaments():
    """Get all tournaments"""
    db = await get_database()
    tournaments = await db.tournaments.find().to_list(1000)
    return [{
        "id": str(t["_id"]),
        **{k: v for k, v in t.items() if k != "_id"}
    } for t in tournaments]

@router.get("/{tournament_id}/matches", response_model=List[Match])
async def get_tournament_matches(tournament_id: str):
    """Get all matches for a specific tournament"""
    db = await get_database()
    matches = await db.matches.find({"tournament_id": tournament_id}).sort("date", -1).to_list(1000)
    return [Match(**await match_helper(match, db)) for match in matches]

@router.get("/{tournament_id}/", response_model=Tournament)
async def get_tournament(tournament_id: str):
    """Get a specific tournament"""
    db = await get_database()
    tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    return Tournament(**tournament_helper(tournament, db))

def tournament_helper(tournament, db):
    return {
        "id": str(tournament["_id"]),
        **{k: v for k, v in tournament.items() if k != "_id"}
    }