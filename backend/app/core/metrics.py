from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import time
from functools import wraps

from app.core.logging import get_logger
from app.db.redis import get_redis

logger = get_logger(__name__)

class MetricsCollector:
    """Collects and stores application metrics."""
    
    def __init__(self):
        self._metrics_prefix = "metrics:"
        self._default_retention = 86400  # 24 hours in seconds
    
    async def increment_counter(self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        try:
            redis = await get_redis()
            key = self._build_metric_key(metric_name, tags)
            await redis.increment_counter(key, self._default_retention)
        except Exception as e:
            logger.error(f"Failed to increment metric {metric_name}: {e}")
    
    async def record_timing(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timing metric in milliseconds."""
        try:
            redis = await get_redis()
            key = self._build_metric_key(metric_name, tags)
            await redis.list_push(f"{key}:timings", value)
            # Keep only last 1000 timing values
            await redis.list_trim(f"{key}:timings", 0, 999)
        except Exception as e:
            logger.error(f"Failed to record timing {metric_name}: {e}")
    
    def _build_metric_key(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Build Redis key for a metric including tags."""
        key = f"{self._metrics_prefix}{metric_name}"
        if tags:
            tag_str = ".".join(f"{k}={v}" for k, v in sorted(tags.items()))
            key = f"{key}:{tag_str}"
        return key
    
    async def get_counter_value(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get the current value of a counter metric."""
        try:
            redis = await get_redis()
            key = self._build_metric_key(metric_name, tags)
            value = await redis.get_cache(key)
            return int(value) if value is not None else 0
        except Exception as e:
            logger.error(f"Failed to get counter {metric_name}: {e}")
            return 0
    
    async def get_timing_stats(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get statistics for a timing metric."""
        try:
            redis = await get_redis()
            key = self._build_metric_key(metric_name, tags)
            timings = await redis.list_range(f"{key}:timings", 0, -1)
            
            if not timings:
                return {"count": 0, "avg": 0, "min": 0, "max": 0}
            
            values = [float(t) for t in timings]
            return {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values)
            }
        except Exception as e:
            logger.error(f"Failed to get timing stats {metric_name}: {e}")
            return {"count": 0, "avg": 0, "min": 0, "max": 0}

# Singleton instance
metrics = MetricsCollector()

def track_timing(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """Decorator to track function execution time."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = (time.time() - start_time) * 1000  # Convert to milliseconds
                await metrics.record_timing(metric_name, duration, tags)
        return wrapper
    return decorator
