import os
from datetime import datetime
from typing import Dict, List, Optional, Union

from bson import ObjectId
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

app = FastAPI()

# MongoDB connection
client = AsyncIOMotorClient(
    os.getenv("MONGO_URI", "mongodb://mongodb:27017/fifa_rivalry")
)
db = client.fifa_rivalry


# Pydantic models
class PlayerCreate(BaseModel):
    name: str


class Player(PlayerCreate):
    id: str
    total_matches: int = 0
    total_goals_scored: int = 0
    total_goals_conceded: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    points: int = 0


class MatchCreate(BaseModel):
    player1_id: str
    player2_id: str
    player1_goals: int
    player2_goals: int


class Match(BaseModel):
    id: str
    player1_name: str
    player2_name: str
    player1_goals: int
    player2_goals: int
    date: datetime


class HeadToHeadStats(BaseModel):
    player1_name: str
    player2_name: str
    total_matches: int
    player1_wins: int
    player2_wins: int
    draws: int
    player1_goals: int
    player2_goals: int
    player1_win_rate: float
    player2_win_rate: float
    player1_avg_goals: float
    player2_avg_goals: float


class PlayerDetailedStats(BaseModel):
    id: str
    name: str
    total_matches: int
    total_goals_scored: int
    total_goals_conceded: int
    wins: int
    losses: int
    draws: int
    points: int
    win_rate: float
    average_goals_scored: float
    average_goals_conceded: float
    highest_wins_against: Optional[Dict[str, int]]
    highest_losses_against: Optional[Dict[str, int]]
    winrate_over_time: List[Dict[str, Union[datetime, float]]]


# Helper functions
def player_helper(player) -> dict:
    return {
        "id": str(player["_id"]),
        "name": player["name"],
        "total_matches": player["total_matches"],
        "total_goals_scored": player["total_goals_scored"],
        "total_goals_conceded": player["total_goals_conceded"],
        "wins": player["wins"],
        "losses": player["losses"],
        "draws": player["draws"],
        "points": player["points"],
    }


async def match_helper(match) -> dict:
    player1 = await db.players.find_one({"_id": ObjectId(match["player1_id"])})
    player2 = await db.players.find_one({"_id": ObjectId(match["player2_id"])})
    return {
        "id": str(match["_id"]),
        "player1_name": player1["name"],
        "player2_name": player2["name"],
        "player1_goals": match["player1_goals"],
        "player2_goals": match["player2_goals"],
        "date": match["date"],
    }


@app.post("/players", response_model=Player)
async def register_player(player: PlayerCreate):
    existing_player = await db.players.find_one({"name": player.name})
    if existing_player:
        raise HTTPException(
            status_code=400, detail="A player with this name already exists"
        )

    player_data = player.dict()
    player_data.update(
        {
            "total_matches": 0,
            "total_goals_scored": 0,
            "total_goals_conceded": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "points": 0,
        }
    )
    new_player = await db.players.insert_one(player_data)
    created_player = await db.players.find_one({"_id": new_player.inserted_id})
    return player_helper(created_player)


@app.post("/matches", response_model=Match)
async def record_match(match: MatchCreate):
    player1 = await db.players.find_one({"_id": ObjectId(match.player1_id)})
    player2 = await db.players.find_one({"_id": ObjectId(match.player2_id)})

    if not player1 or not player2:
        raise HTTPException(status_code=404, detail="One or both players not found")

    match_dict = match.dict()
    match_dict["date"] = datetime.now()
    new_match = await db.matches.insert_one(match_dict)

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
        await db.players.update_one({"_id": player["_id"]}, update)

    created_match = await db.matches.find_one({"_id": new_match.inserted_id})
    return Match(**await match_helper(created_match))


@app.get("/players", response_model=List[Player])
async def get_players():
    players = await db.players.find().to_list(1000)
    return [player_helper(player) for player in players]


@app.get("/stats", response_model=List[Player])
async def get_stats():
    players = await db.players.find().sort("points", -1).to_list(1000)
    return [player_helper(player) for player in players]


@app.get("/matches", response_model=List[Match])
async def get_matches():
    matches = await db.matches.find().sort("date", -1).to_list(1000)
    return [Match(**await match_helper(match)) for match in matches]


@app.get("/player/{player_id}/matches", response_model=List[Match])
async def get_player_matches(player_id: str):
    matches = (
        await db.matches.find(
            {"$or": [{"player1_id": player_id}, {"player2_id": player_id}]}
        )
        .sort("date", -1)
        .to_list(1000)
    )
    return [Match(**await match_helper(match)) for match in matches]


@app.get("/head-to-head/{player1_id}/{player2_id}", response_model=HeadToHeadStats)
async def get_head_to_head_stats(player1_id: str, player2_id: str):
    player1 = await db.players.find_one({"_id": ObjectId(player1_id)})
    player2 = await db.players.find_one({"_id": ObjectId(player2_id)})

    if not player1 or not player2:
        raise HTTPException(status_code=404, detail="One or both players not found")

    matches = await db.matches.find(
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


@app.get("/player/{player_id}/stats", response_model=PlayerDetailedStats)
async def get_player_detailed_stats(player_id: str):
    player = await db.players.find_one({"_id": ObjectId(player_id)})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    matches = (
        await db.matches.find(
            {"$or": [{"player1_id": player_id}, {"player2_id": player_id}]}
        )
        .sort("date", 1)
        .to_list(1000)
    )

    wins_against = {}
    losses_against = {}

    for match in matches:
        opponent_id = (
            match["player2_id"]
            if match["player1_id"] == player_id
            else match["player1_id"]
        )
        opponent = await db.players.find_one({"_id": ObjectId(opponent_id)})

        if match["player1_id"] == player_id:
            if match["player1_goals"] > match["player2_goals"]:
                wins_against[opponent["name"]] = (
                    wins_against.get(opponent["name"], 0) + 1
                )
            elif match["player1_goals"] < match["player2_goals"]:
                losses_against[opponent["name"]] = (
                    losses_against.get(opponent["name"], 0) + 1
                )
        else:
            if match["player2_goals"] > match["player1_goals"]:
                wins_against[opponent["name"]] = (
                    wins_against.get(opponent["name"], 0) + 1
                )
            elif match["player2_goals"] < match["player1_goals"]:
                losses_against[opponent["name"]] = (
                    losses_against.get(opponent["name"], 0) + 1
                )

    highest_wins = (
        max(wins_against.items(), key=lambda x: x[1]) if wins_against else None
    )
    highest_losses = (
        max(losses_against.items(), key=lambda x: x[1]) if losses_against else None
    )

    # Calculate winrate over time
    total_matches = 0
    total_wins = 0
    winrate_over_time = []

    for match in matches:
        total_matches += 1
        is_player1 = match["player1_id"] == player_id
        player_goals = match["player1_goals"] if is_player1 else match["player2_goals"]
        opponent_goals = (
            match["player2_goals"] if is_player1 else match["player1_goals"]
        )

        if player_goals > opponent_goals:
            total_wins += 1

        winrate = total_wins / total_matches if total_matches > 0 else 0
        winrate_over_time.append({"date": match["date"], "winrate": winrate})

    stats = player_helper(player)
    stats.update(
        {
            "win_rate": (
                player["wins"] / player["total_matches"]
                if player["total_matches"] > 0
                else 0
            ),
            "average_goals_scored": (
                player["total_goals_scored"] / player["total_matches"]
                if player["total_matches"] > 0
                else 0
            ),
            "average_goals_conceded": (
                player["total_goals_conceded"] / player["total_matches"]
                if player["total_matches"] > 0
                else 0
            ),
            "highest_wins_against": (
                {highest_wins[0]: highest_wins[1]} if highest_wins else None
            ),
            "highest_losses_against": (
                {highest_losses[0]: highest_losses[1]} if highest_losses else None
            ),
            "winrate_over_time": winrate_over_time,
        }
    )

    return PlayerDetailedStats(**stats)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
