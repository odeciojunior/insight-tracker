import logging
from fastapi import FastAPI
from app.core.config import settings
from app.db.base import init_databases, close_databases
from app.api.router import api_router
from app.middleware.cache import CacheMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)

# Add middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CacheMiddleware)

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    try:
        await init_databases()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on application shutdown."""
    try:
        await close_databases()
        logger.info("Application shut down successfully")
    except Exception as e:
        logger.error(f"Error during application shutdown: {str(e)}")
        raise

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Check application health."""
    from app.db.base import check_database_health
    return {
        "status": "ok",
        "version": settings.VERSION,
        "databases": await check_database_health()
    }
