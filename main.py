
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
        "authentication": {
            "register": f"{settings.API_V1_STR}/auth/register",
            "login": f"{settings.API_V1_STR}/auth/login",
            "login_json": f"{settings.API_V1_STR}/auth/login-json"
        }
    }