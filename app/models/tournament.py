from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TournamentCreate(BaseModel):
    name: str
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    player_ids: List[str] = Field(default_factory=list)


class Tournament(TournamentCreate):
    id: str
    matches: List[str] = Field(default_factory=list)
    matches_count: int = 0
