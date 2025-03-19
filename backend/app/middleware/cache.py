from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.redis import get_redis
import hashlib
import json

class CacheMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cache_timeout: int = 300):
        super().__init__(app)
        self.cache_timeout = cache_timeout
    
    async def dispatch(self, request: Request, call_next):
        if request.method != "GET":
            return await call_next(request)
            
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache
        redis = await get_redis()
        cached_response = await redis.get_cache(cache_key)
        
        if cached_response:
            return Response(
                content=cached_response["content"],
                media_type=cached_response["media_type"],
                status_code=cached_response["status_code"]
            )
        
        # Get response from route handler
        response = await call_next(request)
        
        # Cache the response
        if 200 <= response.status_code < 400:
            response_body = [chunk async for chunk in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))
            
            await redis.set_cache(
                cache_key,
                {
                    "content": b"".join(response_body),
                    "media_type": response.media_type,
                    "status_code": response.status_code
                },
                self.cache_timeout
            )
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate unique cache key based on request path and query params."""
        key_parts = [
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        return hashlib.md5(json.dumps(key_parts).encode()).hexdigest()
