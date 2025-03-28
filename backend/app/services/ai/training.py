import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.db.mongodb import get_mongodb
from app.db.redis import get_redis

logger = get_logger(__name__)

class ModelTrainer:
    """Manages training and fine-tuning of AI models."""
    
    def __init__(self):
        self.base_model_name = "all-MiniLM-L6-v2"  # Default base model
        self.model: Optional[SentenceTransformer] = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the base model."""
        try:
            self.model = SentenceTransformer(self.base_model_name)
            logger.info(f"Initialized base model: {self.base_model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def find_similar_insights(
        self,
        query_embedding: List[float],
        user_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar insights using embedding similarity."""
        try:
            mongodb = await get_mongodb()
            
            # Get all user insights with embeddings
            insights = await mongodb.find_many(
                "insights",
                {"user_id": user_id, "embedding": {"$exists": True}}
            )
            
            if not insights:
                return []
            
            # Convert embeddings for comparison
            stored_embeddings = torch.tensor([i["embedding"] for i in insights])
            query_tensor = torch.tensor(query_embedding)
            
            # Calculate cosine similarities
            similarities = util.pytorch_cos_sim(query_tensor, stored_embeddings)[0]
            top_k_indices = torch.topk(similarities, min(top_k, len(insights))).indices
            
            # Return similar insights with scores
            return [
                {
                    "insight_id": str(insights[idx]["_id"]),
                    "title": insights[idx]["title"],
                    "similarity_score": float(similarities[idx]),
                    "created_at": insights[idx]["created_at"]
                }
                for idx in top_k_indices
            ]
            
        except Exception as e:
            logger.error(f"Error finding similar insights: {e}")
            raise
    
    async def update_user_model(self, user_id: str) -> Dict[str, Any]:
        """Update model weights based on user feedback and patterns."""
        # Placeholder for future implementation
        # Will include fine-tuning based on user's specific domain and preferences
        return {
            "status": "pending_implementation",
            "message": "Model personalization will be implemented in future updates"
        }
    
    async def calculate_insight_clustering(
        self,
        user_id: str,
        min_cluster_size: int = 3
    ) -> List[Dict[str, Any]]:
        """Calculate clusters of related insights."""
        try:
            mongodb = await get_mongodb()
            
            # Get user insights with embeddings
            insights = await mongodb.find_many(
                "insights",
                {"user_id": user_id, "embedding": {"$exists": True}}
            )
            
            if len(insights) < min_cluster_size:
                return []
            
            # Convert embeddings to numpy array
            embeddings = np.array([i["embedding"] for i in insights])
            
            # Placeholder for clustering logic
            # Will be enhanced with proper clustering algorithms
            return [
                {
                    "cluster_id": "placeholder",
                    "insights": [str(insight["_id"]) for insight in insights],
                    "center": embeddings.mean(axis=0).tolist()
                }
            ]
            
        except Exception as e:
            logger.error(f"Error calculating insight clusters: {e}")
            raise

# Singleton instance
model_trainer = ModelTrainer()
