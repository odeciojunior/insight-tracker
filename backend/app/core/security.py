from datetime import datetime, timedelta
from typing import Any, Optional, Union
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Contexto de criptografia para senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or 
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise

def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or 
        timedelta(days=7)  # Default 7 days for refresh token
    )
    to_encode.update({
        "exp": expire,
        "token_type": "refresh"
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating refresh token: {e}")
        raise

def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"Error decoding token: {e}")
        raise

class PasswordValidator:
    """Validate password strength."""
    
    MIN_LENGTH = 8
    SPECIAL_CHARS = "!@#$%^&*(),.?\":{}|<>"
    
    @classmethod
    def validate(cls, password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters long"
            
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
            
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
            
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
            
        if not any(c in cls.SPECIAL_CHARS for c in password):
            return False, "Password must contain at least one special character"
            
        return True, None
