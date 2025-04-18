from fastapi import APIRouter, HTTPException
from bson import ObjectId
from typing import List
from ..schemas.tournament import Tournament, TournamentCreate
from ..core.database import tournaments_collection, matches_collection
from ..utils.helpers import match_helper

router = APIRouter()

@router.post("/", response_model=Tournament)
async def create_tournament(tournament: TournamentCreate):
    tournament_dict = tournament.dict()
    new_tournament = await tournaments_collection.insert_one(tournament_dict)
    created_tournament = await tournaments_collection.find_one({"_id": new_tournament.inserted_id})
    return {
        "id": str(created_tournament["_id"]),
        **{k: v for k, v in created_tournament.items() if k != "_id"}
    }

@router.get("/", response_model=List[Tournament])
async def get_tournaments():
    tournaments = await tournaments_collection.find().to_list(1000)
    return [{
        "id": str(t["_id"]),
        **{k: v for k, v in t.items() if k != "_id"}
    } for t in tournaments]

@router.get("/{tournament_id}/matches", response_model=List[Match])
async def get_tournament_matches(tournament_id: str):
    matches = await matches_collection.find({"tournament_id": tournament_id}).sort("date", -1).to_list(1000)
    return [Match(**await match_helper(match)) for match in matches] 