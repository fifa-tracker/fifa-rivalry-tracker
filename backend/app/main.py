import logging
import logging.config
from fastapi import FastAPI
from .config.settings import LOGGING_CONFIG
from .api import players, matches, tournaments

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FIFA Rivalry Tracker",
    description="API for tracking FIFA matches and player statistics",
    version="1.0.0"
)

# Include routers
app.include_router(players.router, prefix="/players", tags=["players"])
app.include_router(matches.router, prefix="/matches", tags=["matches"])
app.include_router(tournaments.router, prefix="/tournaments", tags=["tournaments"])

@app.get("/")
async def home():
    return {"message": "Welcome to FIFA Rivalry Tracker API"} 