
from fastapi import FastAPI, Request
from app.api.v1.router import api_router
from app.api.dependencies import client
from fastapi.middleware.cors import CORSMiddleware
from app.utils.logging import get_logger
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Get logger for this module
logger = get_logger(__name__)

# Create thread pool executor for async logging
logging_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="logging")

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

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming HTTP requests with async logging"""
    start_time = time.time()
    
    # Log request details asynchronously (non-blocking)
    request_log = f"🌐 {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}"
    loop = asyncio.get_event_loop()
    loop.run_in_executor(logging_executor, logger.info, request_log)
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response details asynchronously (non-blocking)
    response_log = f"✅ {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
    loop.run_in_executor(logging_executor, logger.info, response_log)
    
    return response

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
    
    # Log Google OAuth configuration
    logger.info("🔐 Google OAuth Configuration:")
    logger.info(f"   GOOGLE_CLIENT_ID: {settings.GOOGLE_CLIENT_ID}")
    logger.info(f"   GOOGLE_CLIENT_SECRET: {'*' * 20}...{settings.GOOGLE_CLIENT_SECRET[-4:] if settings.GOOGLE_CLIENT_SECRET else 'Not set'}")
    logger.info(f"   GOOGLE_REDIRECT_URI: {settings.GOOGLE_REDIRECT_URI}")
    logger.info(f"   FRONTEND_URL: {settings.FRONTEND_URL}")
    logger.info(f"   MONGO_URI: {settings.MONGO_URI}")
    logger.info(f"   ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    logger.info(f"   LOG_LEVEL: {settings.LOG_LEVEL}")
    logger.info(f"   LOG_FORMAT: {settings.LOG_FORMAT}")
    logger.info(f"   LOG_FILE: {settings.LOG_FILE}")
    logger.info(f"   LOG_DATE_FORMAT: {settings.LOG_DATE_FORMAT}")
    logger.info(f"   API_V1_STR: {settings.API_V1_STR}")
    logger.info(f"   PROJECT_NAME: {settings.PROJECT_NAME}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on app shutdown"""
    logger.info("🔄 Shutting down application...")
    # Shutdown the logging thread pool executor
    logging_executor.shutdown(wait=True)
    logger.info("✅ Logging executor shutdown complete")

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
            "login": f"{settings.API_V1_STR}/auth/login"
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