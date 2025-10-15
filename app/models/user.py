from pydantic import BaseModel, Field
from typing import Optional


class FriendRequest(BaseModel):
    friend_id: str


class FriendResponse(BaseModel):
    message: str
    friend_id: str
    friend_username: str


class NonFriendPlayer(BaseModel):
    id: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    friend_request_sent: bool = False


class UserSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=100, description="Search term for username, first name, or last name")
    limit: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum number of results to return")


class UserSearchResult(BaseModel):
    id: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: str
    is_friend: bool = False
    friend_request_sent: bool = False
    friend_request_received: bool = False
