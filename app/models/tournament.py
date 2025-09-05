from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TournamentCreate(BaseModel):
    name: str
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    player_ids: List[str] = Field(default_factory=list)
    completed: bool = False
    rounds_per_matchup: int = Field(default=2, ge=1, description="Number of times each player plays against each other")


class Tournament(BaseModel):
    id: str
    name: str
    start_date: datetime
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    matches: List[str] = Field(default_factory=list)
    matches_count: int = 0
    player_ids: List[str] = Field(default_factory=list)
    completed: bool = False
    owner_id: Optional[str] = None
    old_format: bool = False
    rounds_per_matchup: int = Field(default=2, ge=1, description="Number of times each player plays against each other")


class TournamentPlayerStats(BaseModel):
    """Model for tournament player statistics"""
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    total_matches: int
    total_goals_scored: int
    total_goals_conceded: int
    goal_difference: int
    wins: int
    losses: int
    draws: int
    points: int
