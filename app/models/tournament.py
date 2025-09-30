from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TournamentCreate(BaseModel):
    name: str
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    player_ids: List[str] = Field(default_factory=list)
    completed: bool = False
    rounds_per_matchup: int = Field(default=2, ge=1, description="Number of times each player plays against each other")


class Tournament(BaseModel):
    id: str
    name: str
    start_date: datetime
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    matches: List[str] = Field(default_factory=list)
    matches_count: int = 0
    player_ids: List[str] = Field(default_factory=list)
    completed: bool = False
    owner_id: Optional[str] = None
    old_format: bool = False
    rounds_per_matchup: int = Field(default=2, ge=1, description="Number of times each player plays against each other")


class TournamentPlayerStats(BaseModel):
    """Model for tournament player statistics"""
    id: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    total_matches: int
    total_goals_scored: int
    total_goals_conceded: int
    goal_difference: int
    wins: int
    losses: int
    draws: int
    points: int
    last_5_matches: List[str] = []  # Array of 5 characters: W (win), L (loss), D (draw), - (no match)


class TournamentPlayer(BaseModel):
    """Model for tournament player without email"""
    id: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
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
    # Friend system fields
    friends: List[str] = []  # List of user IDs who are friends
    friend_requests_sent: List[str] = []  # List of user IDs to whom friend requests were sent
    friend_requests_received: List[str] = []  # List of user IDs from whom friend requests were received
    # Team tracking fields
    last_5_teams: List[str] = []  # List of last 5 teams the user has played with
