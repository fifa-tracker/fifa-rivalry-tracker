import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# MongoDB configuration
MONGODB_URI = {
    "development": "mongodb://localhost:27017/fifa_rivalry",
    "production": "mongodb://mongodb:27017/fifa_rivalry",
}

# Get the appropriate MongoDB URI based on environment
MONGO_URI = os.getenv(f"MONGO_URI_{ENVIRONMENT.upper()}", os.getenv("MONGO_URI", MONGODB_URI[ENVIRONMENT]))

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "pymongo": {"level": "WARNING"},
        "motor": {"level": "WARNING"},
    },
} 