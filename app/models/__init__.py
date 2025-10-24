# Models package - Export all models for easy importing
from .player import User, UserDetailedStats
from .match import MatchCreate, Match, MatchUpdate, HeadToHeadStats, RecentMatch, UserStatsWithMatches
from .tournament import TournamentCreate, Tournament, TournamentPlayerStats, TournamentPlayer
from .auth import UserCreate, User, UserLogin, Token, TokenData, UserInDB, UserDetailedStats
from .user import FriendRequest, FriendResponse, NonFriendPlayer, UserSearchQuery, UserSearchResult, Friend
from .response import StandardResponse, StandardListResponse, StandardPaginatedResponse, success_response, success_list_response, success_paginated_response, error_response
from pydantic import BaseModel
from typing import Generic, TypeVar, List

# Generic type for paginated responses
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic pagination response model"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

__all__ = [
    # Player models
    "User", 
    "UserDetailedStats",
    
    # Match models
    "MatchCreate",
    "Match",
    "MatchUpdate",
    "HeadToHeadStats",
    "RecentMatch",
    "UserStatsWithMatches",
    
    # Tournament models
    "TournamentCreate",
    "Tournament",
    "TournamentPlayerStats",
    "TournamentPlayer",
    
    # Auth models
    "UserCreate",
    "User",
    "UserLogin",
    "Token",
    "TokenData",
    "UserInDB",
    "UserDetailedStats",
    
    # User models
    "FriendRequest",
    "FriendResponse",
    "NonFriendPlayer",
    "UserSearchQuery",
    "UserSearchResult",
    "Friend",
    
    # Response models
    "StandardResponse",
    "StandardListResponse", 
    "StandardPaginatedResponse",
    "success_response",
    "success_list_response",
    "success_paginated_response",
    "error_response",
    
    # Pagination models
    "PaginatedResponse",
]
