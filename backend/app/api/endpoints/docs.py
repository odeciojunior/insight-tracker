from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.core.logging import get_logger
from app.db.mongodb import get_mongodb, MongoDBClient
from app.schemas.base import ResponseStatus

logger = get_logger(__name__)
router = APIRouter()

@router.get("/api-status")
async def get_api_status(
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> Dict[str, Any]:
    """Get detailed API status and database health information."""
    try:
        mongodb_status = await mongodb.check_health()
        collections_info = await mongodb.db.list_collections().to_list(None)
        collection_stats = {
            coll["name"]: await mongodb.count_documents(coll["name"], {})
            for coll in collections_info
        }
        
        return {
            "status": "healthy",
            "database": {
                "mongodb_connected": mongodb_status,
                "collections": collection_stats
            },
            "api_version": "1.0.0",
            "environment": "development"
        }
    except Exception as e:
        logger.error(f"Error getting API status: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/examples/{endpoint_name}")
async def get_endpoint_examples(endpoint_name: str) -> Dict[str, Any]:
    """Get usage examples for specific endpoints."""
    examples = {
        "insights": {
            "create": {
                "method": "POST",
                "url": "/api/insights",
                "body": {
                    "title": "My First Insight",
                    "content": "This is the content of my insight",
                    "tags": ["example", "first"]
                }
            },
            "list": {
                "method": "GET",
                "url": "/api/insights?page=1&size=10&tag=example"
            }
        },
        "relationships": {
            "create": {
                "method": "POST",
                "url": "/api/relationships",
                "body": {
                    "source_id": "insight_id_1",
                    "target_id": "insight_id_2",
                    "relationship_type": "related",
                    "properties": {"strength": 0.8}
                }
            }
        }
    }
    
    return examples.get(endpoint_name, {"error": "No examples found for this endpoint"})

@router.get("/schema/{model_name}")
async def get_model_schema(model_name: str) -> Dict[str, Any]:
    """Get JSON schema for data models."""
    schemas = {
        "insight": {
            "type": "object",
            "required": ["title", "content"],
            "properties": {
                "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 200
                },
                "content": {
                    "type": "string",
                    "minLength": 1
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    }
    
    return schemas.get(model_name, {"error": "Schema not found"})
