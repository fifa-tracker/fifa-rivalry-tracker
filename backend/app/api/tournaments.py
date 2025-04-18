from fastapi import APIRouter, HTTPException
from bson import ObjectId
from typing import List
from ..schemas.tournament import Tournament, TournamentCreate, TournamentEnd
from ..schemas.match import Match
from ..core.database import tournaments_collection, matches_collection
from ..utils.helpers import match_helper
from datetime import datetime

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

@router.put("/{tournament_id}/end", response_model=Tournament)
async def end_tournament(tournament_id: str, tournament_end: TournamentEnd):
    # Validate tournament exists
    tournament = await tournaments_collection.find_one({"_id": ObjectId(tournament_id)})
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Validate tournament is not already ended
    if tournament.get("end_date"):
        raise HTTPException(status_code=400, detail="Tournament is already ended")

    # Update tournament with end date
    update_result = await tournaments_collection.update_one(
        {"_id": ObjectId(tournament_id)},
        {"$set": {"end_date": tournament_end.end_date}}
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=400, detail="Failed to end tournament")

    # Fetch and return updated tournament
    updated_tournament = await tournaments_collection.find_one({"_id": ObjectId(tournament_id)})
    return {
        "id": str(updated_tournament["_id"]),
        **{k: v for k, v in updated_tournament.items() if k != "_id"}
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

