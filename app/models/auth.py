from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List, Union
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: str
    is_active: bool = True
    is_superuser: bool = False
    is_deleted: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    # Player statistics fields
    total_matches: int = 0
    total_goals_scored: int = 0
    total_goals_conceded: int = 0
    goal_difference: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    points: int = 0
    # ELO rating and tournament fields
    elo_rating: int = 1200  # Default ELO rating
    tournaments_played: int = 0
    tournament_ids: List[str] = []  # List of tournament IDs the user has participated in

    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str


class UserDetailedStats(BaseModel):
    id: str
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
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
    # ELO rating and tournament fields
    elo_rating: int
    tournaments_played: int
    tournament_ids: List[str]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    email: str
    username: str


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None 