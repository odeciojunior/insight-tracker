"""
Redis connection module for the Insight Tracker application.

Provides asynchronous access to Redis for caching, rate limiting,
and message brokering for Celery tasks.
"""

import logging
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar
from redis import asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

# Configure logging
logger = logging.getLogger(__name__)

# Generic type for cache values
T = TypeVar('T')

class RedisClient:
    """
    Asynchronous Redis client with retry mechanism and utility methods.
    
    This class provides a wrapper around aioredis for asynchronous Redis operations
    with built-in retry logic and utility functions for common operations.
    """
    
    def __init__(
        self,
        connection_string: str,
        max_connections: int = 10,
        max_retry_attempts: int = 3,
        retry_delay: float = 0.5,
        default_ttl: int = 3600  # 1 hour default TTL
    ):
        """
        Initialize Redis connection.
        
        Args:
            connection_string: Redis connection URI
            max_connections: Maximum number of connections in the pool
            max_retry_attempts: Maximum number of retry attempts on failed operations
            retry_delay: Delay between retry attempts in seconds
            default_ttl: Default time-to-live for cache entries in seconds
        """
        self._connection_string = connection_string
        self._max_connections = max_connections
        self._max_retry_attempts = max_retry_attempts
        self._retry_delay = retry_delay
        self._default_ttl = default_ttl
        
        self._client: Optional[aioredis.Redis] = None
    
    async def connect(self) -> None:
        """
        Establish connection to Redis with retry mechanism.
        """
        for attempt in range(1, self._max_retry_attempts + 1):
            try:
                logger.info(f"Connecting to Redis (attempt {attempt}/{self._max_retry_attempts})...")
                self._client = await aioredis.from_url(
                    self._connection_string,
                    max_connections=self._max_connections,
                    decode_responses=True
                )
                
                # Test connection
                await self._client.ping()
                logger.info("Successfully connected to Redis")
                return
                
            except (ConnectionError, TimeoutError) as e:
                logger.error(f"Failed to connect to Redis (attempt {attempt}/{self._max_retry_attempts}): {str(e)}")
                
                if attempt < self._max_retry_attempts:
                    wait_time = self._retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.critical("Could not establish connection to Redis after multiple attempts")
                    raise
    
    async def close(self) -> None:
        """
        Close Redis connection.
        """
        if self._client:
            logger.info("Closing Redis connection...")
            await self._client.close()
            self._client = None
            logger.info("Redis connection closed successfully")
    
    async def check_health(self) -> bool:
        """
        Check if the Redis connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self._client:
            logger.warning("Health check failed: No Redis client available")
            return False
        
        try:
            # Try to execute a simple command to check the connection
            await self._client.ping()
            logger.debug("Redis health check: Connection is healthy")
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False

    async def _execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute a Redis operation with retry logic.
        
        Args:
            operation: Async function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Any: The result of the operation
        """
        if not self._client:
            raise ConnectionError("Redis client is not connected")
            
        for attempt in range(1, self._max_retry_attempts + 1):
            try:
                return await operation(*args, **kwargs)
            except (RedisError, ConnectionError, TimeoutError) as e:
                logger.warning(f"Redis operation failed (attempt {attempt}/{self._max_retry_attempts}): {str(e)}")
                
                if attempt < self._max_retry_attempts:
                    wait_time = self._retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying operation in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Redis operation failed after maximum retry attempts")
                    raise

    # Cache Operations
    
    async def set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if not a string)
            ttl: Time-to-live in seconds, uses default if None
            
        Returns:
            bool: True if successful
        """
        if ttl is None:
            ttl = self._default_ttl
            
        # Serialize value if not a string
        if not isinstance(value, str):
            value = json.dumps(value)
            
        return await self._execute_with_retry(
            self._client.set, key, value, ex=ttl
        )
    
    async def get_cache(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Any: The cached value, or None if not found
        """
        result = await self._execute_with_retry(self._client.get, key)
        
        if result is None:
            return None
            
        # Try to deserialize as JSON
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            # Return as-is if not valid JSON
            return result
    
    async def delete_cache(self, key: str) -> int:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            int: Number of keys deleted (0 or 1)
        """
        return await self._execute_with_retry(self._client.delete, key)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "user:*:profile")
            
        Returns:
            int: Number of keys deleted
        """
        keys = await self._execute_with_retry(self._client.keys, pattern)
        
        if not keys:
            return 0
            
        return await self._execute_with_retry(self._client.delete, *keys)
    
    async def set_json(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set a JSON value in the cache.
        
        Args:
            key: Cache key
            value: Dictionary to cache as JSON
            ttl: Time-to-live in seconds, uses default if None
            
        Returns:
            bool: True if successful
        """
        return await self.set_cache(key, value, ttl)
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a JSON value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Dict[str, Any]]: The cached JSON object, or None if not found
        """
        result = await self.get_cache(key)
        
        if result is None or not isinstance(result, dict):
            return None
            
        return result
    
    # Rate Limiting
    
    async def increment_counter(self, key: str, ttl: int) -> int:
        """
        Increment a counter and set expiry if not exists.
        Used for rate limiting.
        
        Args:
            key: Counter key
            ttl: Time-to-live in seconds
            
        Returns:
            int: New counter value
        """
        # Increment counter
        counter = await self._execute_with_retry(self._client.incr, key)
        
        # Set expiry if this is the first increment
        if counter == 1:
            await self._execute_with_retry(self._client.expire, key, ttl)
            
        return counter
    
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Check if a rate limit has been exceeded.
        
        Args:
            key: Rate limit key
            limit: Maximum number of requests
            window: Time window in seconds
            
        Returns:
            bool: True if within limit, False if rate limit exceeded
        """
        counter = await self.increment_counter(key, window)
        return counter <= limit
    
    # Distributed Locks
    
    async def acquire_lock(self, lock_name: str, lock_value: str, ttl: int) -> bool:
        """
        Acquire a distributed lock.
        
        Args:
            lock_name: Name of the lock
            lock_value: Unique value to identify owner of the lock
            ttl: Time-to-live for the lock in seconds
            
        Returns:
            bool: True if lock was acquired, False otherwise
        """
        # Use SET NX (Not eXists) to ensure atomic lock acquisition
        result = await self._execute_with_retry(
            self._client.set, f"lock:{lock_name}", lock_value, nx=True, ex=ttl
        )
        return result is not None
    
    async def release_lock(self, lock_name: str, lock_value: str) -> bool:
        """
        Release a distributed lock if owned by this process.
        
        Args:
            lock_name: Name of the lock
            lock_value: Value used when acquiring the lock
            
        Returns:
            bool: True if lock was released, False if not owner or doesn't exist
        """
        lock_key = f"lock:{lock_name}"
        
        # Only release if we own the lock (compare value)
        current_value = await self._execute_with_retry(self._client.get, lock_key)
        
        if current_value != lock_value:
            return False
            
        await self._execute_with_retry(self._client.delete, lock_key)
        return True
    
    # List Operations
    
    async def list_push(self, key: str, value: Any) -> int:
        """
        Push a value to the end of a list.
        
        Args:
            key: List key
            value: Value to push (will be JSON serialized if not a string)
            
        Returns:
            int: Length of the list after push
        """
        # Serialize value if not a string
        if not isinstance(value, str):
            value = json.dumps(value)
            
        return await self._execute_with_retry(self._client.rpush, key, value)
    
    async def list_pop(self, key: str) -> Optional[Any]:
        """
        Pop the first value from a list.
        
        Args:
            key: List key
            
        Returns:
            Optional[Any]: The popped value, or None if list is empty
        """
        result = await self._execute_with_retry(self._client.lpop, key)
        
        if result is None:
            return None
            
        # Try to deserialize as JSON
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            # Return as-is if not valid JSON
            return result
    
    async def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        Get a range of values from a list.
        
        Args:
            key: List key
            start: Start index (0-based)
            end: End index (inclusive), -1 for all
            
        Returns:
            List[Any]: List of values, deserialized if possible
        """
        results = await self._execute_with_retry(self._client.lrange, key, start, end)
        
        # Try to deserialize each value as JSON
        deserialized = []
        for item in results:
            try:
                deserialized.append(json.loads(item))
            except (json.JSONDecodeError, TypeError):
                deserialized.append(item)
                
        return deserialized
    
    # Publish/Subscribe
    
    async def publish(self, channel: str, message: Any) -> int:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel name
            message: Message to publish (will be JSON serialized if not a string)
            
        Returns:
            int: Number of clients that received the message
        """
        # Serialize message if not a string
        if not isinstance(message, str):
            message = json.dumps(message)
            
        return await self._execute_with_retry(self._client.publish, channel, message)

    # Celery Integration
    
    async def celery_task_key_exists(self, task_id: str) -> bool:
        """
        Check if a Celery task result exists.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            bool: True if task result exists, False otherwise
        """
        key = f"celery-task-meta-{task_id}"
        return await self._execute_with_retry(self._client.exists, key) > 0
    
    async def get_celery_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a Celery task result from Redis.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Optional[Dict[str, Any]]: Task result data, or None if not found
        """
        key = f"celery-task-meta-{task_id}"
        return await self.get_json(key)

# Singleton instance of the Redis client
redis_client: Optional[RedisClient] = None

async def init_redis(
    connection_string: str,
    max_connections: int = 10,
    max_retry_attempts: int = 3,
    retry_delay: float = 0.5,
    default_ttl: int = 3600
) -> RedisClient:
    """
    Initialize the Redis client singleton.
    
    Args:
        connection_string: Redis connection URI
        max_connections: Maximum number of connections in the pool
        max_retry_attempts: Maximum number of retry attempts on failed operations
        retry_delay: Delay between retry attempts in seconds
        default_ttl: Default time-to-live for cache entries in seconds
        
    Returns:
        RedisClient: The initialized Redis client instance
    """
    global redis_client
    
    if redis_client is None:
        redis_client = RedisClient(
            connection_string=connection_string,
            max_connections=max_connections,
            max_retry_attempts=max_retry_attempts,
            retry_delay=retry_delay,
            default_ttl=default_ttl
        )
        await redis_client.connect()
    
    return redis_client

async def close_redis() -> None:
    """
    Close the Redis client connection.
    """
    global redis_client
    
    if redis_client:
        await redis_client.close()
        redis_client = None

async def get_redis() -> RedisClient:
    """
    Get the Redis client instance.
    
    Returns:
        RedisClient: The Redis client instance
    
    Raises:
        ConnectionError: If the Redis client has not been initialized
    """
    if redis_client is None:
        raise ConnectionError("Redis client has not been initialized. Call init_redis first.")
    
    return redis_client

class RateLimiter:
    """
    Rate limiter implementation using Redis.
    
    Provides methods to enforce rate limits based on various keys.
    """
    
    def __init__(self, 
                 redis_client: RedisClient,
                 default_limit: int = 100,
                 default_window: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            redis_client: Redis client instance
            default_limit: Default maximum number of requests
            default_window: Default time window in seconds
        """
        self._redis = redis_client
        self._default_limit = default_limit
        self._default_window = default_window
    
    async def check_limit(self, 
                         key: str, 
                         limit: Optional[int] = None,
                         window: Optional[int] = None) -> bool:
        """
        Check if a rate limit has been exceeded.
        
        Args:
            key: Rate limit key
            limit: Maximum number of requests (uses default if None)
            window: Time window in seconds (uses default if None)
            
        Returns:
            bool: True if within limit, False if rate limit exceeded
        """
        limit = limit or self._default_limit
        window = window or self._default_window
        
        return await self._redis.check_rate_limit(key, limit, window)
    
    async def check_limit_for_ip(self, 
                                ip: str, 
                                action: str = "default",
                                limit: Optional[int] = None,
                                window: Optional[int] = None) -> bool:
        """
        Check if a rate limit for an IP address has been exceeded.
        
        Args:
            ip: IP address
            action: Action name to include in the rate limit key
            limit: Maximum number of requests (uses default if None)
            window: Time window in seconds (uses default if None)
            
        Returns:
            bool: True if within limit, False if rate limit exceeded
        """
        key = f"rate-limit:ip:{ip}:{action}"
        return await self.check_limit(key, limit, window)
    
    async def check_limit_for_user(self, 
                                  user_id: str, 
                                  action: str = "default",
                                  limit: Optional[int] = None,
                                  window: Optional[int] = None) -> bool:
        """
        Check if a rate limit for a user has been exceeded.
        
        Args:
            user_id: User ID
            action: Action name to include in the rate limit key
            limit: Maximum number of requests (uses default if None)
            window: Time window in seconds (uses default if None)
            
        Returns:
            bool: True if within limit, False if rate limit exceeded
        """
        key = f"rate-limit:user:{user_id}:{action}"
        return await self.check_limit(key, limit, window)
