from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel


class PlayerCreate(BaseModel):
    name: str


class Player(PlayerCreate):
    id: str
    total_matches: int = 0
    total_goals_scored: int = 0
    total_goals_conceded: int = 0
    goal_difference: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    points: int = 0


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
