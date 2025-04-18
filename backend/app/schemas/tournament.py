from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, validator

class TournamentCreate(BaseModel):
    name: str
    start_date: datetime
    end_date: Optional[datetime] = None
    description: Optional[str] = None

    def __init__(self, **data):
        data['start_date'] = datetime.now()
        super().__init__(**data)

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Tournament name cannot be empty")
        return v

    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if v is not None and 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v

class TournamentEnd(BaseModel):
    end_date: datetime

    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v

class Tournament(BaseModel):
    id: str
    name: str
    start_date: datetime
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    matches_count: int = 0

    @validator('id')
    def id_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Tournament ID cannot be empty")
        return v

    @validator('matches_count')
    def matches_count_must_not_be_negative(cls, v):
        if v < 0:
            raise ValueError("Matches count cannot be negative")
        return v 