from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from .base import TimestampMixin

class InsightBase(BaseModel):
    """Base schema for insight data."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    tags: Optional[List[str]] = Field(default_factory=list)
    source_type: str = Field(default="text", pattern="^(text|audio|image)$")

class InsightCreate(InsightBase):
    """Schema for creating a new insight."""
    pass

class InsightUpdate(BaseModel):
    """Schema for updating an insight."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class InsightInDB(InsightBase, TimestampMixin):
    """Schema for insight as stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    embedding: Optional[List[float]] = None

class InsightResponse(InsightInDB):
    """Schema for insight response to API requests."""
    relationship_count: Optional[int] = 0
