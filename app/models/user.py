from pydantic import BaseModel
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
