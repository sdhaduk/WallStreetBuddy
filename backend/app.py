"""
WallStreetBuddy FastAPI Application
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from api.config import settings
from api.routers import health, ticker, analysis
from api.services.scheduler_service import scheduler_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager
    Handles startup and shutdown events
    """

    logger.info("🚀 Starting WallStreetBuddy FastAPI application")

    # Check if we should start the scheduler (API-only mode vs scheduler mode)
    scheduler_disabled = os.getenv('DISABLE_SCHEDULER', 'false').lower() == 'true'

    if scheduler_disabled:
        logger.info("📵 Scheduler disabled - running in API-only mode")
        scheduler_started = False
    else:
        try:
            # Start the scheduler service
            await scheduler_service.start()
            logger.info("✅ Scheduler service started successfully")
            scheduler_started = True
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler service: {e}")
            raise

    yield  # FastAPI application runs here

    logger.info("🛑 Shutting down WallStreetBuddy FastAPI application")

    if scheduler_started:
        try:
            await scheduler_service.stop()
            logger.info("✅ Scheduler service stopped successfully")
        except Exception as e:
            logger.error(f"❌ Failed to stop scheduler service: {e}")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
app.include_router(ticker.router, prefix=settings.api_prefix, tags=["ticker"])
app.include_router(analysis.router, prefix=settings.api_prefix, tags=["analysis"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "WallStreetBuddy API",
        "version": settings.api_version,
        "docs": "/docs"
    }

@app.exception_handler(Exception)
async def global_exception_handler(_request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.debug
    )