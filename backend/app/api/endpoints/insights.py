from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Path
from typing import List, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.db.mongodb import get_mongodb, MongoDBClient
from app.schemas.insight import (
    InsightCreate, 
    InsightUpdate, 
    InsightResponse, 
    InsightInDB
)
from app.schemas.base import PaginatedResponse, PageParams
from app.api.dependencies import CurrentUser, RateLimiter

logger = get_logger(__name__)
router = APIRouter()

@router.post("/", response_model=InsightResponse)
async def create_insight(
    insight: InsightCreate,
    current_user: CurrentUser,
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> InsightResponse:
    """Create a new insight."""
    if not await rate_limiter.check_limit_for_user(current_user.id, "create_insight"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    insight_data = insight.model_dump()
    insight_data["user_id"] = current_user.id
    insight_data["created_at"] = datetime.utcnow()
    
    try:
        insight_id = await mongodb.insert_one("insights", insight_data)
        created_insight = await mongodb.find_one("insights", {"_id": insight_id})
        return InsightResponse(**created_insight)
    except Exception as e:
        logger.error(f"Failed to create insight: {e}")
        raise HTTPException(status_code=500, detail="Failed to create insight")

@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: str = Path(..., description="The ID of the insight to retrieve"),
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> InsightResponse:
    """Get a specific insight by ID."""
    insight = await mongodb.find_one("insights", {"_id": insight_id})
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    return InsightResponse(**insight)

@router.get("/", response_model=PaginatedResponse[InsightResponse])
async def list_insights(
    pagination: PageParams = Depends(),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    current_user: CurrentUser = None,
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> PaginatedResponse[InsightResponse]:
    """List insights with pagination and filtering."""
    query = {}
    if current_user:  # Only show user's own insights if authenticated
        query["user_id"] = current_user.id
    if tag:
        query["tags"] = tag
    if search:
        query["$text"] = {"$search": search}
        
    total = await mongodb.count_documents("insights", query)
    insights = await mongodb.find_many(
        "insights",
        query,
        skip=(pagination.page - 1) * pagination.size,
        limit=pagination.size,
        sort=[("created_at", -1)]
    )
    
    return PaginatedResponse(
        items=[InsightResponse(**insight) for insight in insights],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=(total + pagination.size - 1) // pagination.size
    )

@router.put("/{insight_id}", response_model=InsightResponse)
async def update_insight(
    insight_update: InsightUpdate,
    insight_id: str = Path(..., description="The ID of the insight to update"),
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> InsightResponse:
    """Update an existing insight."""
    update_data = insight_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    result = await mongodb.update_one(
        "insights",
        {"_id": insight_id},
        {"$set": update_data}
    )
    
    if not result["matched_count"]:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    updated_insight = await mongodb.find_one("insights", {"_id": insight_id})
    return InsightResponse(**updated_insight)

@router.delete("/{insight_id}")
async def delete_insight(
    insight_id: str = Path(..., description="The ID of the insight to delete"),
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> dict:
    """Delete an insight."""
    result = await mongodb.delete_one("insights", {"_id": insight_id})
    if not result:
        raise HTTPException(status_code=404, detail="Insight not found")
    return {"message": "Insight deleted successfully"}

@router.post("/audio", response_model=InsightResponse)
async def create_insight_from_audio(
    audio_file: UploadFile = File(...),
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> InsightResponse:
    """Create a new insight from an audio file."""
    # This endpoint will be implemented later with Celery task processing
    raise HTTPException(status_code=501, detail="Not implemented yet")
