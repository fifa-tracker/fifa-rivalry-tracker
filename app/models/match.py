from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MatchCreate(BaseModel):
    player1_id: str
    player2_id: str
    player1_goals: int
    player2_goals: int
    tournament_id: str
    team1: str
    team2: str
    half_length: int = Field(ge=3, le=6, description="Match half length in minutes (3-6 minutes)")


class Match(BaseModel):
    id: str
    player1_name: str
    player2_name: str
    player1_goals: int
    player2_goals: int
    date: datetime
    team1: Optional[str] = None
    team2: Optional[str] = None
    tournament_name: Optional[str] = None
    half_length: int


class MatchUpdate(BaseModel):
    player1_goals: int
    player2_goals: int
    half_length: int = Field(ge=3, le=6, description="Match half length in minutes (3-6 minutes)")


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