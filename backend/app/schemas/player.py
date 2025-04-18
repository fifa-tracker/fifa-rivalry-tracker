from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, validator

class PlayerCreate(BaseModel):
    name: str

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Player name cannot be empty")
        return v

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

    @validator('id')
    def id_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Player ID cannot be empty")
        return v

    @validator('total_matches', 'total_goals_scored', 'total_goals_conceded', 
              'wins', 'losses', 'draws', 'points')
    def stats_must_not_be_negative(cls, v):
        if v < 0:
            raise ValueError("Statistics cannot be negative")
        return v

    @validator('total_matches')
    def matches_must_equal_sum(cls, v, values):
        if 'wins' in values and 'losses' in values and 'draws' in values:
            if v != (values['wins'] + values['losses'] + values['draws']):
                raise ValueError("Total matches must equal sum of wins, losses, and draws")
        return v

    @validator('goal_difference')
    def goal_difference_must_match(cls, v, values):
        if 'total_goals_scored' in values and 'total_goals_conceded' in values:
            if v != (values['total_goals_scored'] - values['total_goals_conceded']):
                raise ValueError("Goal difference must equal goals scored minus goals conceded")
        return v

class PlayerDetailedStats(Player):
    win_rate: float = 0.0
    average_goals_scored: float = 0.0
    average_goals_conceded: float = 0.0
    highest_wins_against: Optional[Dict[str, int]] = None
    highest_losses_against: Optional[Dict[str, int]] = None
    winrate_over_time: Optional[List[Dict[str, Union[datetime, float]]]] = None

    @validator('win_rate')
    def win_rate_must_be_between_0_and_1(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Win rate must be between 0 and 1")
        return v

    @validator('average_goals_scored', 'average_goals_conceded')
    def average_goals_must_not_be_negative(cls, v):
        if v < 0:
            raise ValueError("Average goals cannot be negative")
        return v 