
from fastapi import FastAPI
from app.api.v1.router import api_router
from app.api.dependencies import client
from fastapi.middleware.cors import CORSMiddleware
from app.utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)

from app.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Log CORS configuration for debugging
logger.info(f"CORS Origins configured: {settings.CORS_ORIGINS}")

# Ensure CORS origins are clean (no duplicates, no wildcards mixed with specific origins)
clean_origins = []
for origin in settings.CORS_ORIGINS:
    if origin and origin != "*":
        if origin not in clean_origins:
            clean_origins.append(origin)

logger.info(f"Clean CORS Origins: {clean_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=clean_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test the actual connection
@app.on_event("startup")
async def startup_event():
    try:
        # This will actually test the connection
        await client.admin.command('ping')
        logger.info("✅ MongoDB Atlas connection successful!")
    except Exception as e:
        logger.error(f"❌ MongoDB Atlas connection failed: {str(e)}")
        logger.error("Please check:")
        logger.error("1. Your internet connection")
        logger.error("2. MongoDB Atlas IP whitelist settings")
        logger.error("3. Username and password in connection string")
        logger.error("4. Database name in connection string")

# Root endpoint (public - no authentication required)
@app.get("/")
async def root():
    return {
        "message": settings.PROJECT_NAME, 
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "cors_origins": settings.CORS_ORIGINS,
        "authentication": {
            "register": f"{settings.API_V1_STR}/auth/register",
            "login": f"{settings.API_V1_STR}/auth/login",
            "login_json": f"{settings.API_V1_STR}/auth/login-json"
        }
    }

# CORS debug endpoint
@app.get("/cors-debug")
async def cors_debug():
    return {
        "cors_origins": settings.CORS_ORIGINS,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    }

# Simple CORS test endpoint
@app.get("/cors-test")
async def cors_test():
    return {"message": "CORS is working!", "timestamp": "2024-01-01T00:00:00Z"}