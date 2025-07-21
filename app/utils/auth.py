from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from app.models.auth import TokenData, UserInDB
from app.api.dependencies import get_database
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Security configuration
from app.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(username=username, user_id=user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """Get the current authenticated user"""
    token = credentials.credentials
    token_data = verify_token(token)
    
    db = await get_database()
    user = await db.users.find_one({"username": token_data.username})
    logger.debug(f"User found: {user}")
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert MongoDB document to UserInDB model
    user_data = {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "name": user.get("name"),
        "is_active": user.get("is_active", True),
        "is_superuser": user.get("is_superuser", False),
        "is_deleted": user.get("is_deleted", False),
        "created_at": user.get("created_at", datetime.utcnow()),
        "updated_at": user.get("updated_at", datetime.utcnow()),
        "deleted_at": user.get("deleted_at"),
        "hashed_password": user["hashed_password"],
        # Player statistics fields
        "total_matches": user.get("total_matches", 0),
        "total_goals_scored": user.get("total_goals_scored", 0),
        "total_goals_conceded": user.get("total_goals_conceded", 0),
        "goal_difference": user.get("goal_difference", 0),
        "wins": user.get("wins", 0),
        "losses": user.get("losses", 0),
        "draws": user.get("draws", 0),
        "points": user.get("points", 0),
        # ELO rating and tournament fields
        "elo_rating": user.get("elo_rating", 1200),
        "tournaments_played": user.get("tournaments_played", 0),
        "tournament_ids": user.get("tournament_ids", []),
    }
    
    return UserInDB(**user_data)


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Check if user is deleted
    if hasattr(current_user, 'is_deleted') and current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account has been deleted"
        )
    
    return current_user


async def get_current_superuser(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get the current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def user_helper(user: dict) -> dict:
    """Helper function to format user data"""
    # Check if user is deleted
    is_deleted = user.get("is_deleted", False)
    
    return {
        "id": str(user["_id"]),
        "username": "Deleted Player" if is_deleted else user["username"],
        "email": user["email"] if not is_deleted else "deleted@example.com",
        "name": user.get("name"),
        "is_active": user.get("is_active", True),
        "is_superuser": user.get("is_superuser", False),
        "is_deleted": is_deleted,
        "created_at": user.get("created_at", datetime.utcnow()),
        "updated_at": user.get("updated_at", datetime.utcnow()),
        "deleted_at": user.get("deleted_at"),
        # Player statistics fields
        "total_matches": user.get("total_matches", 0),
        "total_goals_scored": user.get("total_goals_scored", 0),
        "total_goals_conceded": user.get("total_goals_conceded", 0),
        "goal_difference": user.get("goal_difference", 0),
        "wins": user.get("wins", 0),
        "losses": user.get("losses", 0),
        "draws": user.get("draws", 0),
        "points": user.get("points", 0),
        # ELO rating and tournament fields
        "elo_rating": user.get("elo_rating", 1200),
        "tournaments_played": user.get("tournaments_played", 0),
        "tournament_ids": user.get("tournament_ids", []),
    } 