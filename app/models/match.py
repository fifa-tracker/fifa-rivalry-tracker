from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MatchCreate(BaseModel):
    player1_id: str
    player2_id: str
    player1_goals: int
    player2_goals: int
    tournament_id: Optional[str] = None
    team1: str
    team2: str
    half_length: int = Field(ge=3, le=6, description="Match half length in minutes (3-6 minutes)")
    completed: bool = False


class Match(BaseModel):
    id: str
    player1_name: str
    player2_name: str
    player1_goals: int
    player2_goals: int
    date: datetime
    team1: Optional[str] = None
    team2: Optional[str] = None
    tournament_name: Optional[str] = None
    half_length: int
    completed: bool = False


class MatchUpdate(BaseModel):
    player1_goals: int
    player2_goals: int
    team1: Optional[str] = None
    team2: Optional[str] = None
    half_length: int = Field(ge=3, le=6, description="Match half length in minutes (3-6 minutes)")
    completed: bool = False


class RecentMatch(BaseModel):
    date: datetime
    player1_goals: int
    player2_goals: int
    tournament_name: Optional[str] = None
    team1: Optional[str] = None
    team2: Optional[str] = None
    opponent_id: Optional[str] = None
    opponent_username: Optional[str] = None
    opponent_first_name: Optional[str] = None
    opponent_last_name: Optional[str] = None
    # Player identification fields
    current_player_id: Optional[str] = None  # The player we're getting stats for
    current_player_username: Optional[str] = None
    current_player_goals: Optional[int] = None  # Goals scored by current player
    opponent_goals: Optional[int] = None  # Goals scored by opponent
    match_result: Optional[str] = None  # "win", "loss", or "draw" from current player's perspective


class HeadToHeadStats(BaseModel):
    player1_id: str
    player2_id: str
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
    recent_matches: List[RecentMatch] = []


class UserStatsWithMatches(BaseModel):
    """User stats along with their last 5 matches"""
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
    elo_rating: int
    tournaments_played: int
    last_5_teams: List[str] = []
    last_5_matches: List[RecentMatch] = [] 