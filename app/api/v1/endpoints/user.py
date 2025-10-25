from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId
from datetime import datetime
from itertools import groupby

from app.models.auth import User, UserInDB, UserCreate, UserUpdate
from app.models.user import FriendRequest, FriendResponse, NonFriendPlayer, UserSearchQuery, UserSearchResult, Friend
from app.models import UserDetailedStats, Match, UserStatsWithMatches, RecentMatch
from app.models.response import success_response, success_list_response, StandardResponse, StandardListResponse
from app.api.dependencies import get_database
from app.utils.auth import get_current_active_user, user_helper, get_password_hash
from app.utils.helpers import match_helper

router = APIRouter()


# User Management Endpoints (moved from players.py)

@router.post("/register", response_model=StandardResponse[User])
async def register_user(user: UserCreate, current_user: UserInDB = Depends(get_current_active_user)):
    """Register a new user"""
    db = await get_database()
    
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": user.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_data = user.dict()
    user_data.update({
        "hashed_password": get_password_hash(user.password),
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        # Initialize player statistics
        "total_matches": 0,
        "total_goals_scored": 0,
        "total_goals_conceded": 0,
        "goal_difference": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "points": 0,
        # ELO rating and tournament fields
        "elo_rating": 1200,
        "tournaments_played": 0,
        "tournament_ids": [],
        # Friend system fields
        "friends": [],
        "friend_requests_sent": [],
        "friend_requests_received": [],
        # Team tracking fields
        "last_5_teams": []
    })
    
    # Remove plain password from data
    del user_data["password"]
    
    # Insert user into database
    result = await db.users.insert_one(user_data)
    
    # Get created user
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    return success_response(
        data=User(**user_helper(created_user)),
        message="User registered successfully"
    )


@router.get("/", response_model=StandardListResponse[User])
async def get_users(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all active users (excluding deleted ones)"""
    db = await get_database()
    users = await db.users.find({"is_deleted": {"$ne": True}}).to_list(1000)
    processed_users = [user_helper(user) for user in users]
    return success_list_response(
        items=processed_users,
        message=f"Retrieved {len(processed_users)} users"
    )


# Social Features Endpoints - must come before /{user_id} to avoid route conflicts

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
    
    # Get opponent details
    opponent_objects = await db.users.find(
        {"_id": {"$in": [ObjectId(oid) for oid in non_friend_opponent_ids]}}
    ).to_list(length=None)
    
    opponents = [
        NonFriendPlayer(
            id=str(opponent["_id"]),
            username=opponent["username"],
            first_name=opponent.get("first_name"),
            last_name=opponent.get("last_name")
        )
        for opponent in opponent_objects
    ]
    
    return success_list_response(
        items=opponents,
        message=f"Retrieved {len(opponents)} recent non-friend opponents"
    )


@router.get("/{user_id}", response_model=StandardResponse[UserStatsWithMatches])
async def get_user(user_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get a specific user by ID with their last 5 matches (including deleted users)"""
    db = await get_database()
    
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's last 5 completed matches
        user_matches = await db.matches.find({
            "$or": [
                {"player1_id": user_id},
                {"player2_id": user_id}
            ],
            "completed": True
        }).sort("date", -1).limit(5).to_list(5)
        
        # Convert matches to RecentMatch format
        recent_matches = []
        for match in user_matches:
            # Get tournament name if available
            tournament_name = None
            if match.get("tournament_id"):
                tournament = await db.tournaments.find_one({"_id": ObjectId(match["tournament_id"])})
                if tournament:
                    tournament_name = tournament.get("name")
            
            # Get opponent information
            opponent_id = match["player2_id"] if match["player1_id"] == user_id else match["player1_id"]
            opponent = await db.users.find_one({"_id": ObjectId(opponent_id)})
            
            # Determine current user's goals and opponent's goals
            current_user_goals = match["player1_goals"] if match["player1_id"] == user_id else match["player2_goals"]
            opponent_goals = match["player2_goals"] if match["player1_id"] == user_id else match["player1_goals"]
            
            # Determine match result from current user's perspective
            if current_user_goals > opponent_goals:
                match_result = "win"
            elif current_user_goals < opponent_goals:
                match_result = "loss"
            else:
                match_result = "draw"
            
            recent_match = RecentMatch(
                date=match["date"],
                player1_goals=match["player1_goals"],
                player2_goals=match["player2_goals"],
                tournament_name=tournament_name,
                team1=match.get("team1"),
                team2=match.get("team2"),
                opponent_id=opponent_id,
                opponent_username=opponent.get("username") if opponent else None,
                opponent_first_name=opponent.get("first_name") if opponent else None,
                opponent_last_name=opponent.get("last_name") if opponent else None,
                current_player_id=user_id,
                current_player_username=user.get("username"),
                current_player_goals=current_user_goals,
                opponent_goals=opponent_goals,
                match_result=match_result
            )
            recent_matches.append(recent_match)
        
        # Create UserStatsWithMatches response
        user_stats = UserStatsWithMatches(
            id=str(user["_id"]),
            username=user["username"],
            first_name=user.get("first_name"),
            last_name=user.get("last_name"),
            total_matches=user.get("total_matches", 0),
            total_goals_scored=user.get("total_goals_scored", 0),
            total_goals_conceded=user.get("total_goals_conceded", 0),
            goal_difference=user.get("goal_difference", 0),
            wins=user.get("wins", 0),
            losses=user.get("losses", 0),
            draws=user.get("draws", 0),
            points=user.get("points", 0),
            elo_rating=user.get("elo_rating", 1200),
            tournaments_played=user.get("tournaments_played", 0),
            last_5_teams=user.get("last_5_teams", []),
            last_5_matches=recent_matches
        )
        
        return success_response(
            data=user_stats,
            message="User information retrieved successfully"
        )
        
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}", response_model=StandardResponse[User])
async def update_user(user_id: str, user: UserUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    """Update a user's information (partial update - only provided fields will be updated)"""
    db = await get_database()
    
    # Check if user exists
    existing_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is deleted
    if existing_user.get("is_deleted", False):
        raise HTTPException(status_code=400, detail="Cannot update a deleted user")

    # Check if new username already exists (if different from current)
    if user.username is not None and user.username != existing_user.get("username"):
        existing_username = await db.users.find_one({"username": user.username})
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already exists")

    # Check if new email already exists (if different from current)
    if user.email is not None and user.email != existing_user.get("email"):
        existing_email = await db.users.find_one({"email": user.email})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

    # Update user data
    update_data = {}
    if user.username is not None:
        update_data["username"] = user.username
    if user.email is not None:
        update_data["email"] = user.email
    if user.first_name is not None:
        update_data["first_name"] = user.first_name
    if user.last_name is not None:
        update_data["last_name"] = user.last_name

    # Check if any fields are being updated
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()
    
    update_result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="User update failed")

    # Get updated user
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    return success_response(
        data=user_helper(updated_user),
        message="User updated successfully"
    )


@router.delete("/{user_id}", response_model=StandardResponse[dict])
async def delete_user(user_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Mark a user as deleted instead of actually deleting them"""
    db = await get_database()
    
    try:
        # Check if user exists
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Mark user as deleted instead of actually deleting
        update_data = {
            "is_active": False,
            "is_deleted": True,
            "deleted_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        update_result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail="User deletion failed")

        return success_response(
            data={"message": "User marked as deleted successfully"},
            message="User marked as deleted successfully"
        )
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        raise


@router.get("/{user_id}/stats", response_model=StandardResponse[UserDetailedStats])
async def get_user_detailed_stats(user_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get detailed statistics for a specific user with their last 5 matches (including deleted users)"""
    db = await get_database()
    
    user : User = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all matches for this user
    matches: List[Match] = await db.matches.find({
        "$or": [
            {"player1_id": user_id},
            {"player2_id": user_id}
        ]
    }).sort("date", 1).to_list(1000)

    wins_against = {}
    losses_against = {}

    for match in matches:
        opponent_id = (
            match["player2_id"]
            if match["player1_id"] == user_id
            else match["player1_id"]
        )
        opponent : User = await db.users.find_one({"_id": ObjectId(opponent_id)})

        if match["player1_id"] == user_id:
            if match["player1_goals"] > match["player2_goals"]:
                wins_against[opponent["username"]] = (
                    wins_against.get(opponent["username"], 0) + 1
                )
            elif match["player1_goals"] < match["player2_goals"]:
                losses_against[opponent["username"]] = (
                    losses_against.get(opponent["username"], 0) + 1
                )
        else:
            if match["player2_goals"] > match["player1_goals"]:
                wins_against[opponent["username"]] = (
                    wins_against.get(opponent["username"], 0) + 1
                )
            elif match["player2_goals"] < match["player1_goals"]:
                losses_against[opponent["username"]] = (
                    losses_against.get(opponent["username"], 0) + 1
                )

    highest_wins = (
        max(wins_against.items(), key=lambda x: x[1]) if wins_against else None
    )
    highest_losses = (
        max(losses_against.items(), key=lambda x: x[1]) if losses_against else None
    )

    # Calculate winrate over time (per day)
    total_matches = 0
    total_wins = 0
    daily_winrate = []

    # Convert match dates to datetime objects if they're strings
    for match in matches:
        if isinstance(match["date"], str):
            match["date"] = datetime.fromisoformat(match["date"])

    # Group matches by date
    for date, day_matches in groupby(matches, key=lambda x: x["date"].date()):
        day_matches = list(day_matches)
        for match in day_matches:
            total_matches += 1
            is_player1 = match["player1_id"] == user_id
            player_goals = (
                match["player1_goals"] if is_player1 else match["player2_goals"]
            )
            opponent_goals = (
                match["player2_goals"] if is_player1 else match["player1_goals"]
            )

            if player_goals > opponent_goals:
                total_wins += 1

        winrate = total_wins / total_matches if total_matches > 0 else 0
        # Convert date to datetime at midnight
        date_dt = datetime.combine(date, datetime.min.time())
        daily_winrate.append({"date": date_dt, "winrate": winrate})

    # Calculate tournament participation
    tournaments_played = 0
    tournament_ids = []
    
    # Find all tournaments where this user is a participant
    tournaments = await db.tournaments.find({
        "player_ids": {"$in": [user_id]}
    }).to_list(1000)
    
    tournaments_played = len(tournaments)
    tournament_ids = [str(t["_id"]) for t in tournaments]
    
    stats = user_helper(user)
    stats.update(
        {
            "win_rate": (
                user["wins"] / user["total_matches"]
                if user["total_matches"] > 0
                else 0
            ),
            "average_goals_scored": (
                user["total_goals_scored"] / user["total_matches"]
                if user["total_matches"] > 0
                else 0
            ),
            "average_goals_conceded": (
                user["total_goals_conceded"] / user["total_matches"]
                if user["total_matches"] > 0
                else 0
            ),
            "highest_wins_against": (
                {highest_wins[0]: highest_wins[1]} if highest_wins else None
            ),
            "highest_losses_against": (
                {highest_losses[0]: highest_losses[1]} if highest_losses else None
            ),
            "winrate_over_time": daily_winrate,
            "tournaments_played": tournaments_played,
            "tournament_ids": tournament_ids,
        }
    )

    # Get user's last 5 completed matches
    user_matches = await db.matches.find({
        "$or": [
            {"player1_id": user_id},
            {"player2_id": user_id}
        ],
        "completed": True
    }).sort("date", -1).limit(5).to_list(5)
    
    # Convert matches to RecentMatch format
    recent_matches = []
    for match in user_matches:
        # Get tournament name if available
        tournament_name = None
        if match.get("tournament_id"):
            tournament = await db.tournaments.find_one({"_id": ObjectId(match["tournament_id"])})
            if tournament:
                tournament_name = tournament.get("name")
        
        # Get opponent information
        opponent_id = match["player2_id"] if match["player1_id"] == user_id else match["player1_id"]
        opponent = await db.users.find_one({"_id": ObjectId(opponent_id)})
        
        # Determine current user's goals and opponent's goals
        current_user_goals = match["player1_goals"] if match["player1_id"] == user_id else match["player2_goals"]
        opponent_goals = match["player2_goals"] if match["player1_id"] == user_id else match["player1_goals"]
        
        # Determine match result from current user's perspective
        if current_user_goals > opponent_goals:
            match_result = "win"
        elif current_user_goals < opponent_goals:
            match_result = "loss"
        else:
            match_result = "draw"
        
        recent_match = RecentMatch(
            date=match["date"],
            player1_goals=match["player1_goals"],
            player2_goals=match["player2_goals"],
            tournament_name=tournament_name,
            team1=match.get("team1"),
            team2=match.get("team2"),
            opponent_id=opponent_id,
            opponent_username=opponent.get("username") if opponent else None,
            opponent_first_name=opponent.get("first_name") if opponent else None,
            opponent_last_name=opponent.get("last_name") if opponent else None,
            current_player_id=user_id,
            current_player_username=user.get("username"),
            current_player_goals=current_user_goals,
            opponent_goals=opponent_goals,
            match_result=match_result
        )
        recent_matches.append(recent_match)
    
    # Add last_5_matches to stats
    stats["last_5_matches"] = recent_matches
    
    # Return the detailed stats with calculated averages
    return success_response(
        data=stats,
        message="User detailed statistics retrieved successfully"
    )


@router.get("/{user_id}/matches", response_model=StandardListResponse[Match])
async def get_user_matches(user_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get all matches for a specific user (including deleted users)"""
    db = await get_database()
    
    # Get user info
    user : User = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    matches = (
        await db.matches.find(
            {"$or": [{"player1_id": user_id}, {"player2_id": user_id}]}
        )
        .sort("date", -1)
        .to_list(1000)
    )

    # Return matches with user names
    matches_with_names = []
    for match in matches:
        match_data = await match_helper(match, db)
        matches_with_names.append(match_data)

    return success_list_response(
        items=matches_with_names,
        message=f"Retrieved {len(matches_with_names)} matches for user"
    )


# Social Features Endpoints

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