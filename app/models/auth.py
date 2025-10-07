from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, List, Union
from datetime import datetime
from enum import Enum


class OAuthProvider(str, Enum):
    """OAuth provider types"""
    GOOGLE = "google"
    LOCAL = "local"


class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class GoogleOAuthUser(BaseModel):
    """Google OAuth user data"""
    google_id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture: Optional[str] = None
    verified_email: bool = False


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email address")
    password: str


class User(UserBase):
    id: str
    is_active: bool = True
    is_superuser: bool = False
    is_deleted: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    # OAuth fields
    oauth_provider: Optional[OAuthProvider] = OAuthProvider.LOCAL
    oauth_id: Optional[str] = None  # Google ID, etc.
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
    # Friend system fields
    friends: List[str] = []  # List of user IDs who are friends
    friend_requests_sent: List[str] = []  # List of user IDs to whom friend requests were sent
    friend_requests_received: List[str] = []  # List of user IDs from whom friend requests were received
    # Team tracking fields
    last_5_teams: List[str] = []  # List of last 5 teams the user has played with

    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: Optional[str] = None  # Optional for OAuth users


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


class GoogleOAuthCallback(BaseModel):
    """Google OAuth callback data"""
    code: str
    state: Optional[str] = None 