from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, validator
from bson import ObjectId

class MatchCreate(BaseModel):
    player1_id: str
    player2_id: str
    player1_goals: int
    player2_goals: int
    team1: str
    team2: str
    # tournament_id: Optional[str] = None
    tournament_id: str

    @validator('player1_id', 'player2_id')
    def player_ids_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Player IDs cannot be empty")
        return v

    @validator('player2_id')
    def players_must_be_different(cls, v, values):
        if 'player1_id' in values and v == values['player1_id']:
            raise ValueError("Players must be different")
        return v

    @validator('player1_goals', 'player2_goals')
    def goals_must_not_be_negative(cls, v):
        if v < 0:
            raise ValueError("Goals cannot be negative")
        return v

    @validator('team1', 'team2')
    def team_names_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Team names cannot be empty")
        return v

    @validator('tournament_id')
    def tournament_id_must_be_valid(cls, v):
        if not v:
            raise ValueError("Tournament ID cannot be empty")
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid tournament ID format")
        return v

@dataclass
class Match:
    id: str
    player1_name: str
    player2_name: str
    player1_goals: int
    player2_goals: int
    date: datetime
    team1: Optional[str] = None
    team2: Optional[str] = None
    tournament_name: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            raise ValueError("Match ID cannot be empty")
        if not self.player1_name or not self.player2_name:
            raise ValueError("Player names cannot be empty")
        if self.player1_goals < 0 or self.player2_goals < 0:
            raise ValueError("Goals cannot be negative")

@dataclass
class MatchUpdate:
    player1_goals: int
    player2_goals: int

    def __post_init__(self):
        if self.player1_goals < 0 or self.player2_goals < 0:
            raise ValueError("Goals cannot be negative")

@dataclass
class HeadToHeadStats:
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

    def __post_init__(self):
        if not self.player1_name or not self.player2_name:
            raise ValueError("Player names cannot be empty")
        if any(x < 0 for x in [self.total_matches, self.player1_wins, self.player2_wins, self.draws,
                              self.player1_goals, self.player2_goals]):
            raise ValueError("Statistics cannot be negative")
        if not 0 <= self.player1_win_rate <= 1 or not 0 <= self.player2_win_rate <= 1:
            raise ValueError("Win rates must be between 0 and 1")
        if self.player1_avg_goals < 0 or self.player2_avg_goals < 0:
            raise ValueError("Average goals cannot be negative")
        if self.total_matches != (self.player1_wins + self.player2_wins + self.draws):
            raise ValueError("Total matches must equal sum of wins and draws") 