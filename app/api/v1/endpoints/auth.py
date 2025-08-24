from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId
from pydantic import BaseModel

from app.models.auth import UserCreate, User, UserLogin, Token
from app.utils.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_active_user,
    user_helper,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.api.dependencies import get_database

router = APIRouter()


class UsernameCheck(BaseModel):
    username: str


@router.post("/check-username")
async def check_username_exists(username_data: UsernameCheck):
    """Check if a username already exists"""
    db = await get_database()
    
    # Check if username already exists
    existing_user = await db.users.find_one({"username": username_data.username})
    
    return {
        "username": username_data.username,
        "exists": existing_user is not None
    }


@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
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
    from datetime import datetime
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
        "tournament_ids": []
    })
    
    # Remove plain password from data
    del user_data["password"]
    
    # Insert user into database
    result = await db.users.insert_one(user_data)
    
    # Get created user
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    return User(**user_helper(created_user))


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login to get access token"""
    db = await get_database()
    
    # Find user by username or email
    user = await db.users.find_one({
        "$or": [
            {"username": user_data.username},
            {"email": user_data.username}
        ]
    })
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Check if user is deleted
    if user.get("is_deleted", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account has been deleted"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "email": user["email"],
        "username": user["username"]
    }


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """Refresh access token"""
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username, "user_id": current_user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "email": current_user.email,
        "username": current_user.username
    } 