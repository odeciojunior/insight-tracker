from celery import shared_task
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.db.mongodb import get_mongodb
from app.tasks.nlp_tasks import process_text_insight, detect_relationships

logger = get_logger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    queue="high"
)
def process_new_insight(self, insight_id: str) -> Dict[str, Any]:
    """
    Process a newly created insight through the full pipeline.
    
    This task orchestrates the complete processing of an insight:
    1. Text processing and analysis
    2. Entity and keyword extraction
    3. Relationship detection
    4. Update insight with processed data
    """
    try:
        # Get insight data
        mongodb = await get_mongodb()
        insight = await mongodb.find_one("insights", {"_id": insight_id})
        if not insight:
            raise ValueError(f"Insight {insight_id} not found")

        # Process text content
        text_result = await process_text_insight.delay(
            insight_id, 
            insight["content"]
        )

        # Detect relationships
        relationships = await detect_relationships.delay(insight_id)

        # Update insight with processed data
        update_data = {
            "processed_at": datetime.utcnow(),
            "tags": text_result.get("tags", []),
            "embedding": text_result.get("embedding", []),
            "metadata": {
                "processing_status": "completed",
                "detected_relationships": len(relationships),
                "processing_time": text_result.get("processing_time")
            }
        }

        await mongodb.update_one(
            "insights",
            {"_id": insight_id},
            {"$set": update_data}
        )

        return {
            "insight_id": insight_id,
            "status": "success",
            "processing_results": text_result,
            "relationships_detected": len(relationships)
        }

    except Exception as e:
        logger.error(f"Error processing insight {insight_id}: {str(e)}")
        # Update insight with error status
        if mongodb:
            await mongodb.update_one(
                "insights",
                {"_id": insight_id},
                {
                    "$set": {
                        "metadata.processing_status": "failed",
                        "metadata.error": str(e)
                    }
                }
            )
        raise

@shared_task(queue="high")
async def process_audio_insight(
    insight_id: str,
    audio_file_path: str
) -> Dict[str, Any]:
    """
    Process an audio insight through transcription and analysis pipeline.
    
    This task handles:
    1. Audio transcription
    2. Text extraction
    3. Forward to text processing pipeline
    """
    try:
        # Placeholder for audio processing
        # Will be implemented in Phase 3
        return {
            "insight_id": insight_id,
            "status": "not_implemented",
            "message": "Audio processing will be implemented in Phase 3"
        }
    except Exception as e:
        logger.error(f"Error processing audio insight {insight_id}: {str(e)}")
        raise
