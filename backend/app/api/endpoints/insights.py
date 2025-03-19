from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.insight import Insight, InsightContent
from app.models.relationship import Relationship
from app.db.mongodb import get_mongodb
from app.db.neo4j import get_neo4j

router = APIRouter()

@router.post("/", response_model=Insight)
async def create_insight(
    insight: Insight,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new insight."""
    insight.user_id = current_user.id
    await insight.save()
    
    # Create Neo4j node
    neo4j = await get_neo4j()
    await neo4j.create_node(
        label="Insight",
        properties={
            "mongo_id": str(insight.id),
            "title": insight.title,
            "tags": insight.tags,
            "user_id": str(current_user.id)
        }
    )
    
    return insight

@router.get("/", response_model=List[Insight])
async def list_insights(
    skip: int = 0,
    limit: int = 100,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """List insights with optional filtering."""
    mongodb = await get_mongodb()
    
    # Build query
    query = {"user_id": current_user.id}
    if tag:
        query["tags"] = tag
    if search:
        query["$text"] = {"$search": search}
        
    cursor = mongodb.get_collection("insights").find(query)
    cursor = cursor.skip(skip).limit(limit)
    
    return [Insight(**doc) for doc in await cursor.to_list(length=None)]

@router.get("/{insight_id}", response_model=Insight)
async def get_insight(
    insight_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific insight."""
    mongodb = await get_mongodb()
    doc = await mongodb.find_one(
        "insights",
        {"_id": insight_id, "user_id": current_user.id}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Insight not found")
    return Insight(**doc)

@router.put("/{insight_id}", response_model=Insight)
async def update_insight(
    insight_id: str,
    insight_update: Insight,
    current_user: User = Depends(get_current_active_user)
):
    """Update an insight."""
    # Validate ownership
    mongodb = await get_mongodb()
    existing = await mongodb.find_one(
        "insights",
        {"_id": insight_id, "user_id": current_user.id}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    # Update MongoDB
    insight_update.id = insight_id
    insight_update.user_id = current_user.id
    await insight_update.save()
    
    # Update Neo4j
    neo4j = await get_neo4j()
    await neo4j.update_node(
        label="Insight",
        match_properties={"mongo_id": insight_id},
        update_properties={
            "title": insight_update.title,
            "tags": insight_update.tags
        }
    )
    
    return insight_update

@router.delete("/{insight_id}")
async def delete_insight(
    insight_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete an insight."""
    mongodb = await get_mongodb()
    result = await mongodb.delete_one(
        "insights",
        {"_id": insight_id, "user_id": current_user.id}
    )
    if result == 0:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    # Delete from Neo4j
    neo4j = await get_neo4j()
    await neo4j.delete_node(
        label="Insight",
        properties={"mongo_id": insight_id},
        detach=True
    )
    
    return {"status": "success"}
