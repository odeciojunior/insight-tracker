from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from .base import TimestampMixin

class UserBase(BaseModel):
    """Base schema for user data."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """Schema for updating user data."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)

class UserInDB(UserBase, TimestampMixin):
    """Schema for user as stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    hashed_password: str
    is_active: bool = True

class UserResponse(UserBase, TimestampMixin):
    """Schema for user response to API requests."""
    id: str
    is_active: bool

class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: Optional[str] = None
