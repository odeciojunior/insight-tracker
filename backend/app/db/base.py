# Import all models here for SQLAlchemy's metadata
# This file is used for Alembic migrations and creating tables

from sqlalchemy.ext.declarative import declarative_base
import logging
from typing import List
from .mongodb import init_mongodb, close_mongodb, get_mongodb
from .neo4j import init_neo4j, close_neo4j, get_neo4j
from .redis import init_redis, close_redis, get_redis
from ..core.config import settings

# Base class for all models
Base = declarative_base()

logger = logging.getLogger(__name__)

async def init_database_connections():
    """Initialize all database connections."""
    try:
        # Initialize MongoDB
        await init_mongodb(
            connection_string=settings.MONGODB_URL,
            db_name=settings.MONGODB_DB_NAME,
            max_retry_attempts=3
        )
        
        # Initialize Neo4j
        await init_neo4j(
            uri=settings.NEO4J_URL,
            username=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD
        )
        
        # Initialize Redis
        await init_redis(
            connection_string=settings.REDIS_URL,
            max_connections=10
        )
        
        logger.info("All database connections initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize databases: {str(e)}")
        raise

async def init_models():
    """Initialize database models and create necessary indexes."""
    try:
        # Get database clients
        mongodb = await get_mongodb()
        neo4j = await get_neo4j()
        
        # Initialize MongoDB indexes
        from app.models.user import User
        from app.models.insight import Insight
        from app.models.relationship import Relationship
        
        models = [User, Insight, Relationship]
        
        for model in models:
            collection = mongodb.get_collection(model.Config.collection_name)
            for index in model.Config.indexes:
                await collection.create_index(index)
        
        # Initialize Neo4j constraints
        await neo4j.create_constraint(
            label="User",
            property_name="email",
            constraint_type="UNIQUE"
        )
        
        await neo4j.create_constraint(
            label="Insight",
            property_name="mongo_id",
            constraint_type="UNIQUE"
        )
        
        logger.info("Database models initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database models: {str(e)}")
        raise

async def init_databases():
    """Initialize all database connections and models."""
    await init_database_connections()
    await init_models()

async def close_databases():
    """Close all database connections."""
    try:
        await close_mongodb()
        await close_neo4j()
        await close_redis()
        logger.info("All database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")
        raise

async def check_database_health() -> List[dict]:
    """Check health of all database connections."""
    health_checks = []
    
    # Check MongoDB
    try:
        mongodb_health = await (await get_mongodb()).check_health()
        health_checks.append({
            "service": "mongodb",
            "status": "healthy" if mongodb_health else "unhealthy"
        })
    except Exception as e:
        health_checks.append({
            "service": "mongodb",
            "status": "unhealthy",
            "error": str(e)
        })
    
    # Check Neo4j
    try:
        neo4j_health = await (await get_neo4j()).check_health()
        health_checks.append({
            "service": "neo4j",
            "status": "healthy" if neo4j_health else "unhealthy"
        })
    except Exception as e:
        health_checks.append({
            "service": "neo4j",
            "status": "unhealthy",
            "error": str(e)
        })
    
    # Check Redis
    try:
        redis_health = await (await get_redis()).check_health()
        health_checks.append({
            "service": "redis",
            "status": "healthy" if redis_health else "unhealthy"
        })
    except Exception as e:
        health_checks.append({
            "service": "redis",
            "status": "unhealthy",
            "error": str(e)
        })
    
    return health_checks

# Import all models to register them with the Base metadata
# This ensures they are discovered by Alembic for migrations

# For example:
# from app.db.models.user import User
# from app.db.models.insight import Insight
