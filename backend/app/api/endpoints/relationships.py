from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.logging import get_logger
from app.db.neo4j import get_neo4j, Neo4jClient
from app.db.mongodb import get_mongodb, MongoDBClient
from app.schemas.base import PaginatedResponse, PageParams
from app.api.dependencies import CurrentUser, RateLimiter

logger = get_logger(__name__)
router = APIRouter()

@router.post("/")
async def create_relationship(
    source_id: str,
    target_id: str,
    relationship_type: str,
    current_user: CurrentUser,
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    properties: Optional[Dict[str, Any]] = None,
    neo4j: Neo4jClient = Depends(get_neo4j),
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> Dict[str, Any]:
    if not await rate_limiter.check_limit_for_user(current_user.id, "create_relationship"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
    # Verify insights exist and belong to user
    source = await mongodb.find_one("insights", {"_id": source_id, "user_id": current_user.id})
    target = await mongodb.find_one("insights", {"_id": target_id, "user_id": current_user.id})
    
    if not source or not target:
        raise HTTPException(status_code=404, detail="One or both insights not found")
    
    # Create relationship in Neo4j
    try:
        rel = await neo4j.create_relationship(
            from_label="Insight",
            from_properties={"id": source_id},
            to_label="Insight",
            to_properties={"id": target_id},
            relationship_type=relationship_type,
            relationship_properties=properties or {}
        )
        return {"message": "Relationship created successfully", "relationship": rel}
    except Exception as e:
        logger.error(f"Failed to create relationship: {e}")
        raise HTTPException(status_code=500, detail="Failed to create relationship")

@router.get("/mindmap/{insight_id}")
async def get_mindmap(
    insight_id: str = Path(..., description="The ID of the central insight"),
    depth: int = Query(default=2, ge=1, le=5),
    neo4j: Neo4jClient = Depends(get_neo4j)
) -> Dict[str, Any]:
    """Get mindmap data centered on a specific insight."""
    try:
        mindmap_data = await neo4j.get_mindmap_data(insight_id, depth)
        return mindmap_data
    except Exception as e:
        logger.error(f"Failed to get mindmap data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mindmap data")

@router.get("/{insight_id}")
async def get_relationships(
    insight_id: str = Path(..., description="The ID of the insight"),
    relationship_type: Optional[str] = None,
    neo4j: Neo4jClient = Depends(get_neo4j)
) -> List[Dict[str, Any]]:
    """Get all relationships for a specific insight."""
    try:
        relationships = await neo4j.get_relationships(
            from_label="Insight",
            from_properties={"id": insight_id},
            relationship_type=relationship_type
        )
        return relationships
    except Exception as e:
        logger.error(f"Failed to get relationships: {e}")
        raise HTTPException(status_code=500, detail="Failed to get relationships")

@router.delete("/{relationship_id}")
async def delete_relationship(
    relationship_id: str = Path(..., description="The ID of the relationship to delete"),
    neo4j: Neo4jClient = Depends(get_neo4j)
) -> Dict[str, str]:
    """Delete a specific relationship."""
    try:
        success = await neo4j.delete_relationship(relationship_id)
        if not success:
            raise HTTPException(status_code=404, detail="Relationship not found")
        return {"message": "Relationship deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete relationship: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete relationship")
