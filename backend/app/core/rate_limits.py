from typing import Dict, Any
from pydantic import BaseModel
from enum import Enum

class RateLimitTier(str, Enum):
    """Rate limit tiers for different types of users."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"

class RateLimitConfig(BaseModel):
    """Configuration for a rate limit rule."""
    requests: int
    window: int  # in seconds
    description: str

# Default rate limits by tier and endpoint
RATE_LIMITS: Dict[str, Dict[RateLimitTier, RateLimitConfig]] = {
    "create_insight": {
        RateLimitTier.FREE: RateLimitConfig(
            requests=10,
            window=3600,
            description="10 insights per hour"
        ),
        RateLimitTier.BASIC: RateLimitConfig(
            requests=50,
            window=3600,
            description="50 insights per hour"
        ),
        RateLimitTier.PREMIUM: RateLimitConfig(
            requests=200,
            window=3600,
            description="200 insights per hour"
        )
    },
    "create_relationship": {
        RateLimitTier.FREE: RateLimitConfig(
            requests=20,
            window=3600,
            description="20 relationships per hour"
        ),
        RateLimitTier.BASIC: RateLimitConfig(
            requests=100,
            window=3600,
            description="100 relationships per hour"
        ),
        RateLimitTier.PREMIUM: RateLimitConfig(
            requests=500,
            window=3600,
            description="500 relationships per hour"
        )
    },
    "ai_suggestions": {
        RateLimitTier.FREE: RateLimitConfig(
            requests=5,
            window=60,
            description="5 AI suggestions per minute"
        ),
        RateLimitTier.BASIC: RateLimitConfig(
            requests=20,
            window=60,
            description="20 AI suggestions per minute"
        ),
        RateLimitTier.PREMIUM: RateLimitConfig(
            requests=100,
            window=60,
            description="100 AI suggestions per minute"
        )
    }
}

def get_rate_limit(action: str, tier: RateLimitTier = RateLimitTier.FREE) -> RateLimitConfig:
    """Get rate limit configuration for an action and tier."""
    if action not in RATE_LIMITS:
        # Default fallback for undefined actions
        return RateLimitConfig(
            requests=10,
            window=60,
            description="Default: 10 requests per minute"
        )
    return RATE_LIMITS[action][tier]

def get_user_tier(user_id: str) -> RateLimitTier:
    """
    Get the rate limit tier for a user.
    To be enhanced with actual user subscription logic.
    """
    # Placeholder - implement actual user tier logic
    return RateLimitTier.FREE
