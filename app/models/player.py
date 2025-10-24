# Import the actual models from auth.py
from app.models.auth import User, UserDetailedStats

# Export the models
__all__ = ["User", "UserDetailedStats"]
