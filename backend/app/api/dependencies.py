from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging import get_logger
from app.db.mongodb import get_mongodb, MongoDBClient
from app.db.neo4j import get_neo4j, Neo4jClient
from app.db.redis import get_redis, RedisClient, RateLimiter
from app.schemas.user import UserInDB

logger = get_logger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Type aliases for dependency injection
MongoDBDep = Annotated[MongoDBClient, Depends(get_mongodb)]
Neo4jDep = Annotated[Neo4jClient, Depends(get_neo4j)]
RedisDep = Annotated[RedisClient, Depends(get_redis)]

# Rate limiter instance
rate_limiter: Optional[RateLimiter] = None

async def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance."""
    global rate_limiter
    if rate_limiter is None:
        redis = await get_redis()
        rate_limiter = RateLimiter(redis)
    return rate_limiter

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    mongodb: MongoDBDep
) -> UserInDB:
    """Get current authenticated user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await mongodb.find_one("users", {"_id": user_id})
    if user is None:
        raise credentials_exception
        
    return UserInDB(**user)

# Type alias for current user dependency
CurrentUser = Annotated[UserInDB, Depends(get_current_user)]
