"""
Database connection modules for the Insight Tracker application.
"""

import logging
from typing import Callable, Any
from fastapi import FastAPI
from .mongodb import (
    init_mongodb,
    close_mongodb,
    get_mongodb,
    MongoDBClient,
    convert_id
)
from .neo4j import init_neo4j, close_neo4j, get_neo4j
from .redis import (
    init_redis,
    close_redis,
    get_redis,
    RedisClient,
    RateLimiter
)
from .schema_validation import (
    SchemaRegistry,
    SCHEMA_TYPES,
    ASC,
    DESC
)
from ..core.config import settings

logger = logging.getLogger(__name__)

async def connect_to_mongodb() -> None:
    """Initialize MongoDB connection."""
    try:
        await init_mongodb(
            connection_string=str(settings.MONGODB_URL),
            db_name=settings.MONGODB_DB_NAME
        )
        logger.info("MongoDB connection established")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise

async def connect_to_neo4j() -> None:
    """Initialize Neo4j connection."""
    try:
        await init_neo4j(
            uri=settings.NEO4J_URL,
            username=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD
        )
        logger.info("Neo4j connection established")
    except Exception as e:
        logger.error(f"Neo4j connection failed: {e}")
        raise

async def connect_to_redis() -> None:
    """Initialize Redis connection."""
    try:
        await init_redis(
            connection_string=settings.REDIS_URL
        )
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise

async def close_db_connections() -> None:
    """Close all database connections."""
    await close_mongodb()
    await close_neo4j()
    await close_redis()
    logger.info("All database connections closed")

def init_db(app: FastAPI) -> None:
    """Initialize database connections on app startup."""
    
    @app.on_event("startup")
    async def startup_db_clients() -> None:
        await connect_to_mongodb()
        await connect_to_neo4j()
        await connect_to_redis()
        logger.info("All database connections initialized")

    @app.on_event("shutdown")
    async def shutdown_db_clients() -> None:
        await close_db_connections()
        logger.info("All database connections shut down")
