from datetime import datetime
from typing import Optional, List, Dict
from pydantic import Field
from bson import ObjectId
from .base import MongoBaseModel, Neo4jBaseModel

class InsightContent(MongoBaseModel):
    """Content model for storing different types of insight content."""
    content_type: str = Field(..., regex="^(text|audio|image)$")
    raw_content: str
    processed_content: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    embeddings: Optional[List[float]] = None

class Insight(MongoBaseModel):
    """Main insight model for MongoDB storage."""
    user_id: ObjectId
    title: str = Field(..., min_length=1, max_length=200)
    summary: Optional[str] = None
    content: InsightContent
    tags: List[str] = Field(default_factory=list)
    source: str = Field(default="manual")
    engagement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_public: bool = False
    last_processed: Optional[datetime] = None
    
    class Config:
        collection_name = "insights"
        indexes = [
            [("user_id", 1)],
            [("tags", 1)],
            [("created_at", -1)],
            [("title", "text"), ("content.processed_content", "text")]
        ]

class InsightNode(Neo4jBaseModel):
    """Insight model for Neo4j graph representation."""
    title: str
    summary: Optional[str]
    tags: List[str]
    user_id: str  # Reference to MongoDB user ID
    engagement_score: float
    created_at: datetime
    
    class Config:
        node_label = "Insight"
