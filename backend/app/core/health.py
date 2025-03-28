from typing import Dict, Any, List
from datetime import datetime
import psutil
import os

from app.core.logging import get_logger
from app.db.mongodb import get_mongodb
from app.db.neo4j import get_neo4j
from app.db.redis import get_redis

logger = get_logger(__name__)

class HealthCheck:
    """System health check utilities."""
    
    @staticmethod
    async def check_databases() -> Dict[str, bool]:
        """Check health of all database connections."""
        try:
            mongodb = await get_mongodb()
            neo4j = await get_neo4j()
            redis = await get_redis()
            
            return {
                "mongodb": await mongodb.check_health(),
                "neo4j": await neo4j.check_health(),
                "redis": await redis.check_health()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"mongodb": False, "neo4j": False, "redis": False}
    
    @staticmethod
    def check_system_resources() -> Dict[str, Any]:
        """Get system resource usage information."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": disk.percent
                }
            }
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {}
    
    @staticmethod
    def check_process_info() -> Dict[str, Any]:
        """Get current process information."""
        try:
            process = psutil.Process(os.getpid())
            return {
                "pid": process.pid,
                "memory_use": process.memory_info().rss,
                "cpu_percent": process.cpu_percent(interval=1),
                "threads": process.num_threads(),
                "uptime": datetime.now().timestamp() - process.create_time()
            }
        except Exception as e:
            logger.error(f"Process info check failed: {e}")
            return {}

# Singleton instance
health_checker = HealthCheck()
