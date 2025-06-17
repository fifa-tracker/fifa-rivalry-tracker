
import logging
from fastapi import FastAPI
from app.api.v1.router import api_router
from app.api.dependencies import client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FIFA Rivalry Tracker API",
    description="API for tracking FIFA match results and player statistics",
    version="1.0.0"
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

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

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "FIFA Rivalry Tracker API", 
        "version": "1.0.0",
        "docs": "/docs"
    }