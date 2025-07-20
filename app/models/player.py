# Import the actual models from auth.py
from app.models.auth import User as Player, UserDetailedStats as PlayerDetailedStats

# Export the models
__all__ = ["Player", "PlayerDetailedStats"]
