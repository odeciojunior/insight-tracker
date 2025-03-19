from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field
from bson import ObjectId
from .base import MongoBaseModel

class Relationship(MongoBaseModel):
    """Relationship model for storing metadata about insight connections."""
    source_id: ObjectId
    target_id: ObjectId
    relationship_type: str = Field(..., regex="^(related|referenced|inspired|depends_on)$")
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_bidirectional: bool = False
    created_by: str = Field(default="system")  # "system" or "user"
    last_validated: Optional[datetime] = None
    
    class Config:
        collection_name = "relationships"
        indexes = [
            [("source_id", 1), ("target_id", 1)],
            [("relationship_type", 1)],
            [("strength", -1)]
        ]

class RelationshipOperation:
    """Helper class for managing Neo4j relationships."""
    def __init__(self, relationship: Relationship):
        self.relationship = relationship
        
    async def create_in_neo4j(self):
        """Create the relationship in Neo4j."""
        from app.db.neo4j import get_neo4j
        
        neo4j = await get_neo4j()
        props = {
            "type": self.relationship.relationship_type,
            "strength": self.relationship.strength,
            "created_at": self.relationship.created_at.isoformat(),
            "created_by": self.relationship.created_by,
            "metadata": self.relationship.metadata
        }
        
        await neo4j.create_relationship(
            from_label="Insight",
            from_properties={"mongo_id": str(self.relationship.source_id)},
            to_label="Insight",
            to_properties={"mongo_id": str(self.relationship.target_id)},
            relationship_type="RELATED_TO",
            relationship_properties=props
        )
