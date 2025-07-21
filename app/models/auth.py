from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List, Union
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime
    # Player statistics fields
    total_matches: int = 0
    total_goals_scored: int = 0
    total_goals_conceded: int = 0
    goal_difference: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    points: int = 0

    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str


class UserDetailedStats(BaseModel):
    id: str
    username: str
    email: EmailStr
    name: Optional[str] = None
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


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    email: str
    username: str


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None 