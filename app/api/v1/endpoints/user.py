from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId
from datetime import datetime

from app.models.auth import User, UserInDB
from app.models.user import FriendRequest, FriendResponse, NonFriendPlayer, UserSearchQuery, UserSearchResult, Friend
from app.models.response import success_response, success_list_response, StandardResponse, StandardListResponse
from app.api.dependencies import get_database
from app.utils.auth import get_current_active_user, user_helper

router = APIRouter()


@router.post("/send-friend-request", response_model=StandardResponse[FriendResponse])
async def send_friend_request(
    friend_request: FriendRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Send a friend request to another user"""
    db = await get_database()
    
    # Check if the friend exists
    try:
        friend = await db.users.find_one({"_id": ObjectId(friend_request.friend_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid friend ID format"
        )
    
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
    
    return success_response(
        data=FriendResponse(
            message="Friend request sent successfully",
            friend_id=friend_request.friend_id,
            friend_username=friend["username"]
        ),
        message="Friend request sent successfully"
    )


@router.post("/accept-friend-request", response_model=FriendResponse)
async def accept_friend_request(
    friend_request: FriendRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Accept a friend request from another user"""
    db = await get_database()
    
    # Check if the friend exists
    try:
        friend = await db.users.find_one({"_id": ObjectId(friend_request.friend_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid friend ID format"
        )
    
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
        friend_id=friend_request.friend_id,
        friend_username=friend["username"]
    )


@router.post("/reject-friend-request", response_model=FriendResponse)
async def reject_friend_request(
    friend_request: FriendRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Reject a friend request from another user"""
    db = await get_database()
    
    # Check if the friend exists
    try:
        friend = await db.users.find_one({"_id": ObjectId(friend_request.friend_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid friend ID format"
        )
    
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
        friend_id=friend_request.friend_id,
        friend_username=friend["username"]
    )


@router.delete("/remove-friend", response_model=FriendResponse)
async def remove_friend(
    friend_request: FriendRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Remove a friend from your friends list"""
    db = await get_database()
    
    # Check if the friend exists
    try:
        friend = await db.users.find_one({"_id": ObjectId(friend_request.friend_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid friend ID format"
        )
    
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
        friend_id=friend_request.friend_id,
        friend_username=friend["username"]
    )


@router.get("/friends", response_model=StandardListResponse[Friend])
async def get_friends(current_user: UserInDB = Depends(get_current_active_user)):
    """Get list of current user's friends"""
    db = await get_database()
    
    if not current_user.friends:
        return success_list_response(
            items=[],
            message="No friends found"
        )
    
    # Get friend objects
    friend_ids = [ObjectId(friend_id) for friend_id in current_user.friends]
    friends_cursor = db.users.find({"_id": {"$in": friend_ids}})
    friends = await friends_cursor.to_list(length=None)
    
    friend_list = [
        Friend(
            id=str(friend["_id"]),
            username=friend["username"],
            first_name=friend.get("first_name"),
            last_name=friend.get("last_name")
        )
        for friend in friends
    ]
    
    return success_list_response(
        items=friend_list,
        message=f"Retrieved {len(friend_list)} friends"
    )


@router.get("/friend-requests", response_model=StandardResponse[dict])
async def get_friend_requests(current_user: UserInDB = Depends(get_current_active_user)):
    """Get pending friend requests (sent and received)"""
    db = await get_database()
    
    # Get sent friend requests
    sent_requests = []
    if current_user.friend_requests_sent:
        sent_ids = [ObjectId(friend_id) for friend_id in current_user.friend_requests_sent]
        sent_cursor = db.users.find({"_id": {"$in": sent_ids}})
        sent_users = await sent_cursor.to_list(length=None)
        sent_requests = [
            {
                "friend_id": str(user["_id"]),
                "username": user["username"],
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name")
            }
            for user in sent_users
        ]
    
    # Get received friend requests
    received_requests = []
    print(f"Received requests: {{\n    'id': '{current_user.id}',\n    'username': '{current_user.username}',\n    'friend_requests_received': {current_user.friend_requests_received}\n}}")
    if current_user.friend_requests_received:
        received_ids = [ObjectId(friend_id) for friend_id in current_user.friend_requests_received]
        received_cursor = db.users.find({"_id": {"$in": received_ids}})
        received_users = await received_cursor.to_list(length=None)
        received_requests = [
            {
                "friend_id": str(user["_id"]),
                "username": user["username"],
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name")
            }
            for user in received_users
        ]
    
    return success_response(
        data={
            "sent_requests": sent_requests,
            "received_requests": received_requests
        },
        message="Friend requests retrieved successfully"
    )


@router.get("/recent-non-friend-opponents", response_model=StandardListResponse[NonFriendPlayer])
async def get_recent_non_friend_opponents(current_user: UserInDB = Depends(get_current_active_user)):
    """Get usernames and names of people you played with in the last 10 matches but are not friends with"""
    db = await get_database()
    
    # Get the last 10 matches where the current user participated
    recent_matches = (
        await db.matches.find(
            {"$or": [{"player1_id": current_user.id}, {"player2_id": current_user.id}]}
        )
        .sort("date", -1)
        .limit(10)
        .to_list(10)
    )
    
    if not recent_matches:
        return success_list_response(
            items=[],
            message="No recent matches found"
        )
    
    # Extract opponent IDs from the matches
    opponent_ids = set()
    for match in recent_matches:
        if match["player1_id"] == current_user.id:
            opponent_ids.add(match["player2_id"])
        else:
            opponent_ids.add(match["player1_id"])
    
    # Remove current user's friends from opponent IDs
    non_friend_opponent_ids = opponent_ids - set(current_user.friends)
    
    if not non_friend_opponent_ids:
        return success_list_response(
            items=[],
            message="No non-friend opponents found"
        )
    
    # Get opponent user details
    opponent_objects = await db.users.find(
        {"_id": {"$in": [ObjectId(opponent_id) for opponent_id in non_friend_opponent_ids]}}
    ).to_list(len(non_friend_opponent_ids))
    
    # Refresh current user data from database to get latest friend_requests_sent
    updated_user = await db.users.find_one({"_id": ObjectId(current_user.id)})
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert to response format
    non_friend_opponents = []
    for opponent in opponent_objects:
        full_name = None
        if opponent.get("first_name") and opponent.get("last_name"):
            full_name = f"{opponent['first_name']} {opponent['last_name']}"
        elif opponent.get("first_name"):
            full_name = opponent["first_name"]
        elif opponent.get("last_name"):
            full_name = opponent["last_name"]
        
        # Check if a friend request was already sent to this opponent using updated user data
        opponent_id = str(opponent["_id"])
        friend_request_sent = opponent_id in updated_user.get("friend_requests_sent", [])
        
        non_friend_opponents.append(NonFriendPlayer(
            id=opponent_id,
            username=opponent["username"],
            first_name=opponent.get("first_name"),
            last_name=opponent.get("last_name"),
            full_name=full_name,
            friend_request_sent=friend_request_sent
        ))
    
    return success_list_response(
        items=non_friend_opponents,
        message=f"Retrieved {len(non_friend_opponents)} non-friend opponents"
    )


@router.post("/search", response_model=StandardListResponse[UserSearchResult])
async def search_users(
    search_query: UserSearchQuery,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Fuzzy search for users by username, first name, or last name"""
    db = await get_database()
    
    # Create a regex pattern for case-insensitive partial matching
    search_pattern = f".*{search_query.query}.*"
    
    # Build the search query for MongoDB
    search_filter = {
        "$and": [
            {"_id": {"$ne": ObjectId(current_user.id)}},  # Exclude current user
            {"is_deleted": {"$ne": True}},  # Exclude deleted users
            {
                "$or": [
                    {"username": {"$regex": search_pattern, "$options": "i"}},
                    {"first_name": {"$regex": search_pattern, "$options": "i"}},
                    {"last_name": {"$regex": search_pattern, "$options": "i"}},
                    {"email": {"$regex": search_pattern, "$options": "i"}}
                ]
            }
        ]
    }
    
    # Execute the search query
    users_cursor = db.users.find(search_filter).limit(search_query.limit)
    users = await users_cursor.to_list(length=search_query.limit)
    
    # Convert to response format
    search_results = []
    for user in users:
        user_id = str(user["_id"])
        
        # Build full name if available
        full_name = None
        if user.get("first_name") and user.get("last_name"):
            full_name = f"{user['first_name']} {user['last_name']}"
        elif user.get("first_name"):
            full_name = user["first_name"]
        elif user.get("last_name"):
            full_name = user["last_name"]
        
        # Check friendship status
        is_friend = user_id in current_user.friends
        friend_request_sent = user_id in current_user.friend_requests_sent
        friend_request_received = user_id in current_user.friend_requests_received
        
        search_results.append(UserSearchResult(
            id=user_id,
            username=user["username"],
            first_name=user.get("first_name"),
            last_name=user.get("last_name"),
            full_name=full_name,
            is_friend=is_friend,
            friend_request_sent=friend_request_sent,
            friend_request_received=friend_request_received
        ))
    
    return success_list_response(
        items=search_results,
        message=f"Found {len(search_results)} users matching search criteria"
    )