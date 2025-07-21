# Models package - Export all models for easy importing
from .player import Player, PlayerDetailedStats
from .match import MatchCreate, Match, MatchUpdate, HeadToHeadStats
from .tournament import TournamentCreate, Tournament, TournamentPlayerStats
from .auth import UserCreate, User, UserLogin, Token, TokenData, UserInDB

__all__ = [
    # Player models
    "Player", 
    "PlayerDetailedStats",
    
    # Match models
    "MatchCreate",
    "Match",
    "MatchUpdate",
    "HeadToHeadStats",
    
    # Tournament models
    "TournamentCreate",
    "Tournament",
    "TournamentPlayerStats",
    
    # Auth models
    "UserCreate",
    "User",
    "UserLogin",
    "Token",
    "TokenData",
    "UserInDB",
]
