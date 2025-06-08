from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TournamentCreate(BaseModel):
    name: str
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    description: Optional[str] = None


class Tournament(TournamentCreate):
    id: str
    matches_count: int = 0
