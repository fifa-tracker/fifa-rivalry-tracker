# Configuration Guide

This document explains how to configure the FIFA Rivalry Tracker application, including logging settings.

## Environment Variables

Create a `.env` file in the root directory with the following variables:

### Required Configuration

```env
# Environment
ENVIRONMENT=development

# Database
MONGO_URI=mongodb://localhost:27017/fifa_rivalry
# Or for MongoDB Atlas:
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/fifa_rivalry?retryWrites=true&w=majority

# JWT Authentication
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

### Logging Configuration

```env
# Logging Configuration
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Optional: Custom log format
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Optional: Log to file (creates logs directory automatically)
LOG_FILE=logs/app.log
```

### Environment-Specific Configuration

```env
# Development overrides
MONGO_URI_DEVELOPMENT=mongodb://localhost:27017/fifa_rivalry_dev
MONGO_URI_PRODUCTION=mongodb+srv://username:password@cluster.mongodb.net/fifa_rivalry_prod?retryWrites=true&w=majority
```

## Logging Configuration

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical errors that may prevent the application from running

### Log Format Options

Default format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

Available placeholders:
- `%(asctime)s`: Timestamp
- `%(name)s`: Logger name
- `%(levelname)s`: Log level
- `%(message)s`: Log message
- `%(funcName)s`: Function name
- `%(lineno)d`: Line number
- `%(filename)s`: File name

### File Logging

To enable file logging, set the `LOG_FILE` environment variable:

```env
LOG_FILE=logs/app.log
```

The application will automatically create the logs directory if it doesn't exist.

### Examples

#### Development with Debug Logging
```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
LOG_FILE=logs/dev.log
```

#### Production with Error-Only Logging
```env
ENVIRONMENT=production
LOG_LEVEL=ERROR
LOG_FILE=logs/production.log
```

#### Console-Only Logging
```env
LOG_LEVEL=INFO
# Don't set LOG_FILE to log only to console
```

## Configuration Validation

The application validates configuration on startup and will raise errors for:

- Missing required environment variables
- Invalid log levels
- Production environment with default secret key

## Centralized Configuration

All configuration is centralized in `app/config.py` and can be accessed throughout the application:

```python
from app.config import settings

# Access configuration
print(settings.LOG_LEVEL)
print(settings.MONGO_URI)
print(settings.SECRET_KEY)
```

## Logging Usage

Use the centralized logging throughout the application:

```python
from app.utils.logging import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

## Testing Configuration

To test different logging configurations:

1. Set environment variables
2. Restart the application
3. Check logs in console or file

Example:
```bash
LOG_LEVEL=DEBUG LOG_FILE=logs/test.log python -m uvicorn main:app --reload
``` 