from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel

from app.models.auth import User, UserInDB
from app.api.dependencies import get_database
from app.utils.auth import get_current_active_user, user_helper

router = APIRouter()


class FriendRequest(BaseModel):
    friend_username: str


class FriendResponse(BaseModel):
    message: str
    friend_username: str


@router.post("/send-friend-request", response_model=FriendResponse)
async def send_friend_request(
    friend_request: FriendRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Send a friend request to another user"""
    db = await get_database()
    
    # Check if the friend exists
    friend = await db.users.find_one({"username": friend_request.friend_username})
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if trying to send request to self
    if friend["_id"] == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send friend request to yourself"
        )
    
    friend_id = str(friend["_id"])
    
    # Check if already friends
    if friend_id in current_user.friends:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already friends with this user"
        )
    
    # Check if friend request already sent
    if friend_id in current_user.friend_requests_sent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request already sent to this user"
        )
    
    # Check if friend request already received from this user
    if friend_id in current_user.friend_requests_received:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user has already sent you a friend request"
        )
    
    # Add friend request to current user's sent list
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {
            "$addToSet": {"friend_requests_sent": friend_id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    # Add friend request to friend's received list
    await db.users.update_one(
        {"_id": ObjectId(friend_id)},
        {
            "$addToSet": {"friend_requests_received": current_user.id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return FriendResponse(
        message="Friend request sent successfully",
        friend_username=friend_request.friend_username
    )


@router.post("/accept-friend-request", response_model=FriendResponse)
async def accept_friend_request(
    friend_request: FriendRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Accept a friend request from another user"""
    db = await get_database()
    
    # Check if the friend exists
    friend = await db.users.find_one({"username": friend_request.friend_username})
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    friend_id = str(friend["_id"])
    
    # Check if friend request was received from this user
    if friend_id not in current_user.friend_requests_received:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No friend request received from this user"
        )
    
    # Check if already friends
    if friend_id in current_user.friends:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already friends with this user"
        )
    
    # Add friend to both users' friends list
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {
            "$addToSet": {"friends": friend_id},
            "$pull": {"friend_requests_received": friend_id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    await db.users.update_one(
        {"_id": ObjectId(friend_id)},
        {
            "$addToSet": {"friends": current_user.id},
            "$pull": {"friend_requests_sent": current_user.id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return FriendResponse(
        message="Friend request accepted successfully",
        friend_username=friend_request.friend_username
    )


@router.post("/reject-friend-request", response_model=FriendResponse)
async def reject_friend_request(
    friend_request: FriendRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Reject a friend request from another user"""
    db = await get_database()
    
    # Check if the friend exists
    friend = await db.users.find_one({"username": friend_request.friend_username})
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    friend_id = str(friend["_id"])
    
    # Check if friend request was received from this user
    if friend_id not in current_user.friend_requests_received:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No friend request received from this user"
        )
    
    # Remove friend request from both users
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {
            "$pull": {"friend_requests_received": friend_id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    await db.users.update_one(
        {"_id": ObjectId(friend_id)},
        {
            "$pull": {"friend_requests_sent": current_user.id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return FriendResponse(
        message="Friend request rejected successfully",
        friend_username=friend_request.friend_username
    )


@router.delete("/remove-friend", response_model=FriendResponse)
async def remove_friend(
    friend_request: FriendRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Remove a friend from your friends list"""
    db = await get_database()
    
    # Check if the friend exists
    friend = await db.users.find_one({"username": friend_request.friend_username})
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    friend_id = str(friend["_id"])
    
    # Check if they are friends
    if friend_id not in current_user.friends:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not friends with this user"
        )
    
    # Remove friend from both users' friends list
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {
            "$pull": {"friends": friend_id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    await db.users.update_one(
        {"_id": ObjectId(friend_id)},
        {
            "$pull": {"friends": current_user.id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return FriendResponse(
        message="Friend removed successfully",
        friend_username=friend_request.friend_username
    )


@router.get("/friends", response_model=List[User])
async def get_friends(current_user: UserInDB = Depends(get_current_active_user)):
    """Get list of current user's friends"""
    db = await get_database()
    
    if not current_user.friends:
        return []
    
    # Get friend objects
    friend_ids = [ObjectId(friend_id) for friend_id in current_user.friends]
    friends_cursor = db.users.find({"_id": {"$in": friend_ids}})
    friends = await friends_cursor.to_list(length=None)
    
    return [User(**user_helper(friend)) for friend in friends]


@router.get("/friend-requests", response_model=dict)
async def get_friend_requests(current_user: UserInDB = Depends(get_current_active_user)):
    """Get pending friend requests (sent and received)"""
    db = await get_database()
    
    # Get sent friend requests
    sent_requests = []
    if current_user.friend_requests_sent:
        sent_ids = [ObjectId(friend_id) for friend_id in current_user.friend_requests_sent]
        sent_cursor = db.users.find({"_id": {"$in": sent_ids}})
        sent_users = await sent_cursor.to_list(length=None)
        sent_requests = [User(**user_helper(user)) for user in sent_users]
    
    # Get received friend requests
    received_requests = []
    if current_user.friend_requests_received:
        received_ids = [ObjectId(friend_id) for friend_id in current_user.friend_requests_received]
        received_cursor = db.users.find({"_id": {"$in": received_ids}})
        received_users = await received_cursor.to_list(length=None)
        received_requests = [User(**user_helper(user)) for user in received_users]
    
    return {
        "sent_requests": sent_requests,
        "received_requests": received_requests
    }