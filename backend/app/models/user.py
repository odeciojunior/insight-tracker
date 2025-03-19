from datetime import datetime
from typing import Optional, List
from pydantic import EmailStr, Field
from .base import MongoBaseModel, Neo4jBaseModel

class User(MongoBaseModel):
    """User model for MongoDB storage."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    settings: dict = Field(default_factory=dict)
    
    class Config:
        collection_name = "users"
        indexes = [
            [("email", 1), ("unique", True)],
            [("username", 1), ("unique", True)]
        ]

class UserNode(Neo4jBaseModel):
    """User model for Neo4j graph representation."""
    email: EmailStr
    username: str
    created_insights: int = 0
    last_active: Optional[datetime] = None
    
    class Config:
        node_label = "User"
