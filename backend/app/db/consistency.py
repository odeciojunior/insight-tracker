import logging
import asyncio
from typing import Dict, List, Any, Optional
from bson import ObjectId

from app.db.mongodb import mongodb
from app.db.neo4j import neo4j_db

logger = logging.getLogger(__name__)

class DatabaseConsistencyManager:
    """
    Manages consistency between MongoDB and Neo4j.
    """
    
    async def ensure_insight_consistency(self, insight_id: str):
        """
        Ensure that an insight exists in both MongoDB and Neo4j with consistent data.
        
        Args:
            insight_id: ID of the insight to check and fix
        """
        try:
            # Get insight from MongoDB
            mongo_insight = await mongodb.db.insights.find_one({"_id": ObjectId(insight_id)})
            
            # If insight exists in MongoDB but not in Neo4j, create it
            if mongo_insight:
                # Check if exists in Neo4j
                result = await neo4j_db.execute_query(
                    "MATCH (i:Insight {id: $id}) RETURN i",
                    {"id": str(insight_id)}
                )
                
                neo4j_insight_exists = len(result) > 0 if result else False
                
                if not neo4j_insight_exists:
                    logger.info(f"Insight {insight_id} exists in MongoDB but not in Neo4j. Creating in Neo4j...")
                    await self._create_insight_in_neo4j(mongo_insight)
                    
            else:
                # If insight doesn't exist in MongoDB but exists in Neo4j, remove from Neo4j
                result = await neo4j_db.execute_query(
                    "MATCH (i:Insight {id: $id}) RETURN i",
                    {"id": str(insight_id)}
                )
                
                neo4j_insight_exists = len(result) > 0 if result else False
                
                if neo4j_insight_exists:
                    logger.info(f"Insight {insight_id} exists in Neo4j but not in MongoDB. Removing from Neo4j...")
                    await neo4j_db.execute_query(
                        "MATCH (i:Insight {id: $id}) DETACH DELETE i",
                        {"id": str(insight_id)}
                    )
            
            return True
        except Exception as e:
            logger.error(f"Error ensuring insight consistency: {e}")
            return False
    
    async def ensure_relationship_consistency(self, source_id: str, target_id: str):
        """
        Ensure that a relationship between insights is consistent across databases.
        
        Args:
            source_id: Source insight ID
            target_id: Target insight ID
        """
        try:
            # Check if both insights exist in MongoDB
            source = await mongodb.db.insights.find_one({"_id": ObjectId(source_id)})
            target = await mongodb.db.insights.find_one({"_id": ObjectId(target_id)})
            
            if not source or not target:
                # If either insight doesn't exist in MongoDB, ensure relationship
                # doesn't exist in Neo4j
                await neo4j_db.execute_query(
                    """
                    MATCH (s:Insight {id: $source_id})-[r]-(t:Insight {id: $target_id})
                    DELETE r
                    """,
                    {"source_id": str(source_id), "target_id": str(target_id)}
                )
                
                if not source:
                    await neo4j_db.execute_query(
                        "MATCH (s:Insight {id: $id}) DETACH DELETE s",
                        {"id": str(source_id)}
                    )
                
                if not target:
                    await neo4j_db.execute_query(
                        "MATCH (t:Insight {id: $id}) DETACH DELETE t",
                        {"id": str(target_id)}
                    )
            
            return True
        except Exception as e:
            logger.error(f"Error ensuring relationship consistency: {e}")
            return False
    
    async def _create_insight_in_neo4j(self, mongo_insight: Dict[str, Any]):
        """
        Create an insight in Neo4j based on MongoDB data.
        
        Args:
            mongo_insight: Insight data from MongoDB
        """
        insight_id = str(mongo_insight["_id"])
        user_id = str(mongo_insight["user_id"])
        
        # Create basic insight node
        await neo4j_db.execute_query(
            """
            CREATE (i:Insight {
                id: $id,
                title: $title,
                user_id: $user_id,
                created_at: $created_at
            })
            """,
            {
                "id": insight_id,
                "title": mongo_insight["title"],
                "user_id": user_id,
                "created_at": mongo_insight.get("created_at", None)
            }
        )
        
        # Add tags if they exist
        if "tags" in mongo_insight and mongo_insight["tags"]:
            for tag in mongo_insight["tags"]:
                await neo4j_db.execute_query(
                    """
                    MERGE (t:Tag {name: $tag})
                    WITH t
                    MATCH (i:Insight {id: $id})
                    MERGE (i)-[:HAS_TAG]->(t)
                    """,
                    {"tag": tag, "id": insight_id}
                )
    
    async def perform_full_consistency_check(self):
        """
        Perform a full consistency check between MongoDB and Neo4j.
        Should be run periodically or after large data operations.
        """
        logger.info("Starting full consistency check between MongoDB and Neo4j")
        
        try:
            # 1. Get all insights from MongoDB
            mongo_insights = []
            async for insight in mongodb.db.insights.find({}):
                mongo_insights.append({
                    "id": str(insight["_id"]),
                    "data": insight
                })
            
            # 2. Get all insights from Neo4j
            neo4j_insights = await neo4j_db.execute_query(
                "MATCH (i:Insight) RETURN i.id AS id"
            )
            neo4j_ids = set(record["id"] for record in neo4j_insights)
            
            # 3. Sync MongoDB -> Neo4j (create missing in Neo4j)
            mongo_ids = set(insight["id"] for insight in mongo_insights)
            missing_in_neo4j = mongo_ids - neo4j_ids
            
            for insight_id in missing_in_neo4j:
                insight_data = next(i["data"] for i in mongo_insights if i["id"] == insight_id)
                await self._create_insight_in_neo4j(insight_data)
                logger.info(f"Created missing insight {insight_id} in Neo4j")
            
            # 4. Sync Neo4j -> MongoDB (remove orphaned from Neo4j)
            orphaned_in_neo4j = neo4j_ids - mongo_ids
            
            for insight_id in orphaned_in_neo4j:
                await neo4j_db.execute_query(
                    "MATCH (i:Insight {id: $id}) DETACH DELETE i",
                    {"id": insight_id}
                )
                logger.info(f"Removed orphaned insight {insight_id} from Neo4j")
            
            logger.info(f"Consistency check completed: {len(missing_in_neo4j)} created in Neo4j, {len(orphaned_in_neo4j)} removed from Neo4j")
            return True
        
        except Exception as e:
            logger.error(f"Error during consistency check: {e}")
            return False
    
    async def ensure_transaction(self, operations):
        """
        Ensure a set of operations are executed as an atomic transaction across both databases.
        If any operation fails, all are rolled back.
        
        Args:
            operations: A list of operation functions to execute
        """
        # Start recording operations for potential rollback
        mongodb_operations = []
        neo4j_operations = []
        
        try:
            # Execute all operations
            for operation in operations:
                result = await operation()
                if isinstance(result, tuple) and len(result) == 2:
                    mongo_op, neo4j_op = result
                    if mongo_op:
                        mongodb_operations.append(mongo_op)
                    if neo4j_op:
                        neo4j_operations.append(neo4j_op)
            
            return True
        
        except Exception as e:
            logger.error(f"Transaction failed, rolling back: {e}")
            
            # Rollback Neo4j operations (in reverse order)
            async with neo4j_db.transaction() as tx:
                for rollback_op in reversed(neo4j_operations):
                    if callable(rollback_op):
                        await rollback_op(tx)
            
            # Rollback MongoDB operations (in reverse order)
            for rollback_op in reversed(mongodb_operations):
                if callable(rollback_op):
                    await rollback_op()
            
            return False

# Singleton instance
consistency_manager = DatabaseConsistencyManager()
