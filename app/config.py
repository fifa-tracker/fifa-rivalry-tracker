import os
from typing import Optional
from pathlib import Path
from dotenv import dotenv_values

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
config = dotenv_values(env_path) if env_path.exists() else {}

def get_env_var(key: str, default: str = None) -> str:
    """Get environment variable with fallback to .env file"""
    return os.getenv(key, config.get(key, default))

class Settings:
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = get_env_var("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Database
    MONGO_URI: str = (
        get_env_var("MONGO_URI_LOCAL") if ENVIRONMENT == "development" 
        else get_env_var("MONGO_URI") or get_env_var(f"MONGO_URI_{ENVIRONMENT.upper()}")
    )
    DATABASE_NAME: str = "fifa_rivalry"
    
    # JWT Authentication
    SECRET_KEY: str = get_env_var("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(get_env_var("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # React development server
        "http://localhost:8000",  # FastAPI development server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "https://fifa-tracker-web-five.vercel.app",  # New Vercel deployment
    ]
    
    # Allow CORS origins to be overridden by environment variable
    _cors_origins_env = get_env_var("CORS_ORIGINS")
    if _cors_origins_env:
        # Parse CORS origins from environment variable, filtering out wildcards
        origins = []
        for origin in _cors_origins_env.split(","):
            origin = origin.strip()
            if origin and origin != "*":
                origins.append(origin)
        if origins:
            CORS_ORIGINS = origins
    
    # Logging
    LOG_LEVEL: str = get_env_var("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = get_env_var("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE: Optional[str] = get_env_var("LOG_FILE")
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FIFA Rivalry Tracker API"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "API for tracking FIFA match results and player statistics"
    
    # Security
    PASSWORD_MIN_LENGTH: int = 6
    USERNAME_MIN_LENGTH: int = 3
    USERNAME_MAX_LENGTH: int = 50
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = get_env_var("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = get_env_var("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = get_env_var("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
    FRONTEND_URL: str = get_env_var("FRONTEND_URL", "http://localhost:3000")
    
    # ELO Rating
    DEFAULT_ELO_RATING: int = 1200
    ELO_K_FACTOR: int = 32
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    
    @classmethod
    def get_logging_config(cls) -> dict:
        """Get logging configuration"""
        return {
            "level": cls.LOG_LEVEL,
            "format": cls.LOG_FORMAT,
            "date_format": cls.LOG_DATE_FORMAT,
            "file": cls.LOG_FILE,
        }
    
    @classmethod
    def validate(cls) -> None:
        """Validate required settings"""
        if not cls.MONGO_URI:
            raise ValueError("MONGO_URI is required")
        
        if cls.SECRET_KEY == "your-secret-key-here-change-in-production":
            if cls.ENVIRONMENT == "production":
                raise ValueError("SECRET_KEY must be changed in production")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL not in valid_levels:
            raise ValueError(f"Invalid LOG_LEVEL: {cls.LOG_LEVEL}. Must be one of {valid_levels}")

# Create settings instance
settings = Settings()

# Validate settings on import
try:
    settings.validate()
except ValueError as e:
    # Use print here since logging might not be configured yet
    print(f"Configuration error: {e}")
    raise 