from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from datetime import datetime

@dataclass
class PlayerCreate:
    name: str

    def __post_init__(self):
        if not self.name:
            raise ValueError("Player name cannot be empty")

@dataclass
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

    def __post_init__(self):
        super().__post_init__()
        if not self.id:
            raise ValueError("Player ID cannot be empty")
        if any(x < 0 for x in [self.total_matches, self.total_goals_scored, self.total_goals_conceded, 
                              self.wins, self.losses, self.draws, self.points]):
            raise ValueError("Statistics cannot be negative")
        if self.total_matches != (self.wins + self.losses + self.draws):
            raise ValueError("Total matches must equal sum of wins, losses, and draws")
        if self.goal_difference != (self.total_goals_scored - self.total_goals_conceded):
            raise ValueError("Goal difference must equal goals scored minus goals conceded")

@dataclass
class PlayerDetailedStats(Player):
    win_rate: float
    average_goals_scored: float
    average_goals_conceded: float
    highest_wins_against: Optional[Dict[str, int]] = None
    highest_losses_against: Optional[Dict[str, int]] = None
    winrate_over_time: List[Dict[str, Union[datetime, float]]] = None

    def __post_init__(self):
        super().__post_init__()
        if not 0 <= self.win_rate <= 1:
            raise ValueError("Win rate must be between 0 and 1")
        if self.average_goals_scored < 0 or self.average_goals_conceded < 0:
            raise ValueError("Average goals cannot be negative") 