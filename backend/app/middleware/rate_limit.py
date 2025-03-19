from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.redis import get_redis

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app, 
        requests_per_minute: int = 60,
        burst_limit: int = 100
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        redis = await get_redis()

        # Check rate limit
        key = f"rate_limit:{client_ip}"
        requests = await redis.increment_counter(key, 60)

        if requests > self.burst_limit:
            raise HTTPException(
                status_code=429, 
                detail="Too many requests"
            )

        return await call_next(request)
