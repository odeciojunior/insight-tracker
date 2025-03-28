from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.db.mongodb import get_mongodb, MongoDBClient
from app.db.redis import get_redis, RedisClient
from app.schemas.base import ResponseStatus

logger = get_logger(__name__)
router = APIRouter()

@router.get("/suggest/tags/{insight_id}")
async def suggest_tags(
    insight_id: str = Path(...),
    mongodb: MongoDBClient = Depends(get_mongodb),
    redis: RedisClient = Depends(get_redis)
) -> List[str]:
    """Suggest tags for an insight based on its content."""
    # Check cache first
    cache_key = f"tag_suggestions:{insight_id}"
    cached_suggestions = await redis.get_cache(cache_key)
    if cached_suggestions:
        return cached_suggestions
    
    # Get insight content
    insight = await mongodb.find_one("insights", {"_id": insight_id})
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    # Basic tag extraction (to be enhanced with NLP later)
    # Currently just returns common words as tags
    content = insight.get("content", "").lower()
    words = set(word.strip() for word in content.split() if len(word) > 3)
    suggested_tags = list(words)[:5]  # Limit to 5 suggestions
    
    # Cache the results
    await redis.set_cache(cache_key, suggested_tags, ttl=3600)  # Cache for 1 hour
    
    return suggested_tags

@router.get("/suggest/connections/{insight_id}")
async def suggest_connections(
    insight_id: str = Path(...),
    limit: int = Query(default=5, ge=1, le=20),
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> List[Dict[str, Any]]:
    """Suggest potential connections to other insights."""
    insight = await mongodb.find_one("insights", {"_id": insight_id})
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    # Basic content-based suggestion (to be enhanced with embeddings later)
    # Currently just looks for insights with similar tags
    tags = insight.get("tags", [])
    if not tags:
        return []
    
    similar_insights = await mongodb.find_many(
        "insights",
        {
            "_id": {"$ne": insight_id},  # Exclude current insight
            "tags": {"$in": tags}  # Find insights with matching tags
        },
        limit=limit,
        sort=[("created_at", -1)]
    )
    
    return [
        {
            "insight_id": str(similar["_id"]),
            "title": similar["title"],
            "matching_tags": [tag for tag in similar.get("tags", []) if tag in tags],
            "confidence": len([tag for tag in similar.get("tags", []) if tag in tags]) / len(tags)
        }
        for similar in similar_insights
    ]

@router.get("/analyze/{insight_id}")
async def analyze_insight(
    insight_id: str = Path(...),
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> Dict[str, Any]:
    """Analyze an insight and provide insights about it."""
    insight = await mongodb.find_one("insights", {"_id": insight_id})
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    # Basic analysis (to be enhanced with NLP and ML later)
    content = insight.get("content", "")
    words = content.split()
    
    analysis = {
        "length": len(content),
        "word_count": len(words),
        "created_at": insight.get("created_at"),
        "has_tags": bool(insight.get("tags")),
        "source_type": insight.get("source_type", "text"),
        "complexity_score": len(content) / (len(words) + 1)  # Basic readability metric
    }
    
    return analysis

@router.post("/feedback/{insight_id}")
async def submit_feedback(
    insight_id: str = Path(...),
    feedback_type: str = Query(..., enum=["relevant", "not_relevant", "connection"]),
    feedback_data: Dict[str, Any],
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> ResponseStatus:
    """Submit feedback about AI suggestions to improve future recommendations."""
    # Store feedback for future model improvement
    feedback_record = {
        "insight_id": insight_id,
        "feedback_type": feedback_type,
        "feedback_data": feedback_data,
        "timestamp": datetime.utcnow()
    }
    
    try:
        await mongodb.insert_one("ai_feedback", feedback_record)
        return ResponseStatus(
            success=True,
            message="Feedback received successfully"
        )
    except Exception as e:
        logger.error(f"Failed to store feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to store feedback")
