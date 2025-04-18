from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class TournamentCreate:
    name: str
    start_date: datetime
    end_date: datetime
    description: Optional[str] = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("Tournament name cannot be empty")
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")

@dataclass
class Tournament(TournamentCreate):
    id: str
    matches_count: int = 0

    def __post_init__(self):
        super().__post_init__()
        if not self.id:
            raise ValueError("Tournament ID cannot be empty")
        if self.matches_count < 0:
            raise ValueError("Matches count cannot be negative") 