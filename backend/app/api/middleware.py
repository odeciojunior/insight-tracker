from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import uuid
import time

from app.core.logging import get_logger, append_context_to_log
from app.db.redis import get_redis, RateLimiter
from app.core.config import settings

logger = get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
            
        redis = await get_redis()
        limiter = RateLimiter(redis)
        
        # Get client IP and current timestamp
        client_ip = request.client.host
        
        # Check rate limit
        is_allowed = await limiter.check_limit_for_ip(
            ip=client_ip,
            action=request.url.path,
            limit=100,  # 100 requests
            window=60   # per minute
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
            
        return await call_next(request)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware with timing and context."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add context to all log messages within this request
        append_context_to_log(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None
        )
        
        logger.info("Request started")
        
        try:
            response = await call_next(request)
            
            # Log request completion
            process_time = (time.time() - start_time) * 1000
            logger.info(
                "Request completed",
                status_code=response.status_code,
                process_time_ms=round(process_time, 2)
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(round(process_time, 2))
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            logger.exception("Request failed")
            raise
