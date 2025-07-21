import logging
import logging.config
from typing import Optional
from pathlib import Path

import os

# Import settings
try:
    from app.config import settings
except ImportError:
    # Fallback for when config is not available (e.g., during testing)
    class FallbackSettings:
        LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
        LOG_FILE = os.getenv("LOG_FILE")
    
    settings = FallbackSettings()

def get_log_level() -> str:
    """Get log level from settings or use default"""
    return settings.LOG_LEVEL.upper()

def get_log_format() -> str:
    """Get log format from settings or use default"""
    return settings.LOG_FORMAT

def get_log_file() -> Optional[str]:
    """Get log file path from settings"""
    return settings.LOG_FILE

def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    disable_existing_loggers: bool = False
) -> None:
    """
    Setup logging configuration for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log message format string
        log_file: Path to log file (optional)
        disable_existing_loggers: Whether to disable existing loggers
    """
    # Use provided values or get from settings/defaults
    level = log_level or get_log_level()
    format_str = log_format or get_log_format()
    file_path = log_file or get_log_file()
    
    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if level not in valid_levels:
        level = "INFO"
        print(f"Warning: Invalid log level '{log_level}', using '{level}'")
    
    # Create log directory if logging to file
    if file_path:
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    config = {
        "version": 1,
        "disable_existing_loggers": disable_existing_loggers,
        "formatters": {
            "default": {
                "format": format_str,
                "datefmt": settings.LOG_DATE_FORMAT,
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": settings.LOG_DATE_FORMAT,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "default",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": level,
                "handlers": ["console"],
                "propagate": False
            },
            "app": {  # Application logger
                "level": level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {  # Uvicorn logger
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "fastapi": {  # FastAPI logger
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Add file handler if log file is specified
    if file_path:
        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "level": level,
            "formatter": "detailed",
            "filename": file_path,
            "mode": "a"
        }
        
        # Add file handler to loggers
        for logger_name in config["loggers"]:
            config["loggers"][logger_name]["handlers"].append("file")
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {level}, Format: {format_str}")
    if file_path:
        logger.info(f"Log file: {file_path}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

# Initialize logging when module is imported
setup_logging()
