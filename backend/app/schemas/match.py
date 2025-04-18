from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class MatchCreate:
    player1_id: str
    player2_id: str
    player1_goals: int
    player2_goals: int
    team1: str
    team2: str
    tournament_id: Optional[str] = None

    def __post_init__(self):
        if not self.player1_id or not self.player2_id:
            raise ValueError("Player IDs cannot be empty")
        if self.player1_id == self.player2_id:
            raise ValueError("Players must be different")
        if self.player1_goals < 0 or self.player2_goals < 0:
            raise ValueError("Goals cannot be negative")
        if not self.team1 or not self.team2:
            raise ValueError("Team names cannot be empty")

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