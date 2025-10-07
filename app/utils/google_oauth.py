"""
Google OAuth utility functions
"""
import httpx
from typing import Dict, Optional
from fastapi import HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token

from app.config import settings
from app.models.auth import GoogleOAuthUser, OAuthProvider
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def verify_google_token(token: str) -> GoogleOAuthUser:
    """
    Verify Google OAuth token and extract user information
    """
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        # Extract user information
        google_user = GoogleOAuthUser(
            google_id=idinfo['sub'],
            email=idinfo['email'],
            first_name=idinfo.get('given_name'),
            last_name=idinfo.get('family_name'),
            picture=idinfo.get('picture'),
            verified_email=idinfo.get('email_verified', False)
        )
        
        return google_user
        
    except ValueError as e:
        logger.error(f"Invalid Google token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    except Exception as e:
        logger.error(f"Error verifying Google token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying Google token"
        )


async def exchange_code_for_token(code: str) -> Dict[str, str]:
    """
    Exchange authorization code for access token
    """
    token_url = "https://oauth2.googleapis.com/token"
    
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for token"
            )


async def get_google_user_info(access_token: str) -> GoogleOAuthUser:
    """
    Get user information from Google using access token
    """
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(user_info_url, headers=headers)
            response.raise_for_status()
            user_data = response.json()
            
            google_user = GoogleOAuthUser(
                google_id=user_data['id'],
                email=user_data['email'],
                first_name=user_data.get('given_name'),
                last_name=user_data.get('family_name'),
                picture=user_data.get('picture'),
                verified_email=user_data.get('verified_email', False)
            )
            
            return google_user
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error getting Google user info: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from Google"
            )


def generate_google_auth_url(state: Optional[str] = None) -> str:
    """
    Generate Google OAuth authorization URL
    """
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "scope": "openid email profile",
        "response_type": "code",
        "access_type": "offline",
    }
    
    if state:
        params["state"] = state
    
    # Build URL with parameters
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{auth_url}?{param_string}"


async def create_or_get_google_user(google_user: GoogleOAuthUser, db) -> Dict:
    """
    Create a new user or get existing user from Google OAuth data
    """
    from datetime import datetime
    
    # Check if user already exists with this Google ID
    existing_user = await db.users.find_one({
        "oauth_provider": OAuthProvider.GOOGLE,
        "oauth_id": google_user.google_id
    })
    
    if existing_user:
        logger.info(f"Found existing Google user: {existing_user['username']}")
        return existing_user
    
    # Check if user exists with same email
    existing_email_user = await db.users.find_one({"email": google_user.email})
    if existing_email_user:
        # Update existing user to link with Google OAuth
        await db.users.update_one(
            {"_id": existing_email_user["_id"]},
            {
                "$set": {
                    "oauth_provider": OAuthProvider.GOOGLE,
                    "oauth_id": google_user.google_id,
                    "updated_at": datetime.utcnow(),
                    "first_name": google_user.first_name or existing_email_user.get("first_name"),
                    "last_name": google_user.last_name or existing_email_user.get("last_name"),
                }
            }
        )
        logger.info(f"Linked existing user {existing_email_user['username']} with Google OAuth")
        return await db.users.find_one({"_id": existing_email_user["_id"]})
    
    # Create new user
    username = google_user.email.split('@')[0]  # Use email prefix as username
    
    # Ensure username is unique
    counter = 1
    original_username = username
    while await db.users.find_one({"username": username}):
        username = f"{original_username}{counter}"
        counter += 1
    
    user_data = {
        "username": username,
        "email": google_user.email,
        "first_name": google_user.first_name,
        "last_name": google_user.last_name,
        "oauth_provider": OAuthProvider.GOOGLE,
        "oauth_id": google_user.google_id,
        "hashed_password": None,  # No password for OAuth users
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
    }
    
    result = await db.users.insert_one(user_data)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    logger.info(f"Created new Google OAuth user: {username}")
    return created_user
