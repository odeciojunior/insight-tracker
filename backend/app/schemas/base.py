from datetime import datetime
from typing import Optional, Any, TypeVar, Generic, Dict
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")

class TimestampMixin(BaseModel):
    """Mixin for models that need timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class PageParams(BaseModel):
    """Parameters for pagination."""
    page: int = Field(default=1, gt=0)
    size: int = Field(default=10, gt=0, le=100)

class PaginatedResponse(GenericModel, Generic[T]):
    """Generic response model for paginated results."""
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

class ResponseStatus(BaseModel):
    """Standard response status model."""
    success: bool
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
