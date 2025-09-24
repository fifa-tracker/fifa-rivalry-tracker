from fastapi import APIRouter

from .endpoints import players, matches, tournaments, stats, auth, user

# Create the main API v1 router
api_router = APIRouter()

# Include all endpoint routers with their prefixes
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["authentication"]
)

api_router.include_router(
    players.router, 
    prefix="/players", 
    tags=["players"]
)

api_router.include_router(
    matches.router, 
    prefix="/matches", 
    tags=["matches"]
)

api_router.include_router(
    tournaments.router, 
    prefix="/tournaments", 
    tags=["tournaments"]
)

api_router.include_router(
    stats.router, 
    prefix="/stats", 
    tags=["stats"]
)

api_router.include_router(
    user.router, 
    prefix="/user", 
    tags=["user"]
)

# Health check endpoint
@api_router.get("/", tags=["health"])
async def health_check():
    return {"message": "FIFA Rivalry Tracker API v1"}
