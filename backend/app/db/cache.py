"""
Cache utility module for the Insight Tracker application.

Provides decorators and utility functions for caching data in Redis.
"""

import logging
import functools
import hashlib
import json
import inspect
import time
from typing import Any, Dict, Optional, Callable, TypeVar, cast, Union, Tuple

from .redis import get_redis

logger = logging.getLogger(__name__)

# Type variables for decorator functions
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

def make_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """
    Create a cache key from a prefix and arguments.
    
    Args:
        prefix: Key prefix
        *args: Positional arguments to include in the key
        **kwargs: Keyword arguments to include in the key
        
    Returns:
        str: A composed cache key
    """
    # Convert all arguments to a serializable format
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        try:
            key_parts.append(str(arg))
        except Exception:
            # If argument can't be converted to string, use its hash
            key_parts.append(hashlib.md5(str(id(arg)).encode()).hexdigest())
    
    # Add keyword arguments (sorted for consistency)
    if kwargs:
        kwargs_str = json.dumps(
            {k: str(v) for k, v in sorted(kwargs.items())},
            sort_keys=True
        )
        key_parts.append(kwargs_str)
    
    # Join and hash
    key = ":".join(key_parts)
    
    # If key is too long, hash it
    if len(key) > 200:
        key = f"{prefix}:{hashlib.md5(key.encode()).hexdigest()}"
    
    return key

def cache(
    ttl: int = 3600,  # 1 hour default
    prefix: Optional[str] = None,
    key_builder: Optional[Callable[..., str]] = None
) -> Callable[[F], F]:
    """
    Decorator to cache function results in Redis.
    
    Args:
        ttl: Time-to-live for cached value in seconds
        prefix: Key prefix, defaults to function name
        key_builder: Custom key builder function
        
    Returns:
        Callable: Decorated function with caching
    """
    def decorator(func: F) -> F:
        # Use function's qualified name as default prefix
        nonlocal prefix
        if prefix is None:
            prefix = f"{func.__module__}.{func.__qualname__}"
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get key based on function and arguments
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = make_cache_key(prefix, *args, **kwargs)
            
            # Try to get value from cache
            try:
                redis = await get_redis()
                cached_value = await redis.get_cache(cache_key)
                
                if cached_value is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_value
            except Exception as e:
                logger.warning(f"Error getting cached value: {str(e)}")
            
            # Cache miss or error, call the original function
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store the result in cache
            try:
                redis = await get_redis()
                await redis.set_cache(cache_key, result, ttl)
            except Exception as e:
                logger.warning(f"Error caching value: {str(e)}")
            
            return result
        
        return cast(F, wrapper)
    return decorator

class CacheManager:
    """
    Manager for working with cached data.
    
    Provides methods to manipulate cache outside of the cache decorator.
    """
    
    @staticmethod
    async def invalidate(prefix: str, *args: Any, **kwargs: Any) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments for the key
            **kwargs: Keyword arguments for the key
            
        Returns:
            bool: True if cache was invalidated, False otherwise
        """
        try:
            redis = await get_redis()
            cache_key = make_cache_key(prefix, *args, **kwargs)
            result = await redis.delete_cache(cache_key)
            return result > 0
        except Exception as e:
            logger.warning(f"Error invalidating cache: {str(e)}")
            return False
    
    @staticmethod
    async def invalidate_pattern(pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "user:*:profile")
            
        Returns:
            int: Number of cache entries invalidated
        """
        try:
            redis = await get_redis()
            return await redis.invalidate_pattern(pattern)
        except Exception as e:
            logger.warning(f"Error invalidating cache pattern: {str(e)}")
            return 0
    
    @staticmethod
    async def set(prefix: str, value: Any, ttl: int, *args: Any, **kwargs: Any) -> bool:
        """
        Explicitly set a cache value.
        
        Args:
            prefix: Key prefix
            value: Value to cache
            ttl: Time-to-live in seconds
            *args: Positional arguments for the key
            **kwargs: Keyword arguments for the key
            
        Returns:
            bool: True if successful
        """
        try:
            redis = await get_redis()
            cache_key = make_cache_key(prefix, *args, **kwargs)
            return await redis.set_cache(cache_key, value, ttl)
        except Exception as e:
            logger.warning(f"Error setting cache: {str(e)}")
            return False
    
    @staticmethod
    async def get(prefix: str, *args: Any, **kwargs: Any) -> Any:
        """
        Explicitly get a cache value.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments for the key
            **kwargs: Keyword arguments for the key
            
        Returns:
            Any: The cached value, or None if not found
        """
        try:
            redis = await get_redis()
            cache_key = make_cache_key(prefix, *args, **kwargs)
            return await redis.get_cache(cache_key)
        except Exception as e:
            logger.warning(f"Error getting cache: {str(e)}")
            return None

    @staticmethod
    async def get_or_set(
        prefix: str, 
        getter: Callable[[], Any],
        ttl: int = 3600,
        *args: Any, 
        **kwargs: Any
    ) -> Any:
        """
        Get a value from cache or set it if not found.
        
        Args:
            prefix: Key prefix
            getter: Function to call to get the value if not in cache
            ttl: Time-to-live in seconds
            *args: Positional arguments for the key
            **kwargs: Keyword arguments for the key
            
        Returns:
            Any: The cached or newly fetched value
        """
        value = await CacheManager.get(prefix, *args, **kwargs)
        
        if value is None:
            # Get new value
            if inspect.iscoroutinefunction(getter):
                value = await getter()
            else:
                value = getter()
                
            # Store in cache
            await CacheManager.set(prefix, value, ttl, *args, **kwargs)
        
        return value
