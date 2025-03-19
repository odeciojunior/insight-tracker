import logging
import asyncio
from typing import Dict, Any, Optional
import json

from .mongodb import mongodb
from .neo4j import neo4j
from .redis import redis_client

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager for database integrations and consistency."""
    
    async def initialize_databases(self):
        """Initialize and connect to all databases."""
        try:
            # Connect to MongoDB
            await mongodb.connect_to_database()
            
            # Connect to Neo4j
            neo4j.connect_to_database()
            
            # Connect to Redis
            await redis_client.connect()
            
            # Initialize database sync
            await self.verify_database_consistency()
            
            logger.info("All database connections initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
            return False

    async def close_connections(self):
        """Close all database connections."""
        await mongodb.close_database_connection()
        neo4j.close_database_connection()
        await redis_client.close()
        logger.info("All database connections closed.")

    async def check_health(self) -> Dict[str, bool]:
        """Check health of all database connections."""
        return {
            "mongodb": await mongodb.health_check(),
            "neo4j": neo4j.health_check(),
            "redis": await redis_client.health_check()
        }

    async def verify_database_consistency(self):
        """
        Verify and repair consistency between MongoDB and Neo4j.
        This ensures all insights in MongoDB exist in Neo4j.
        """
        logger.info("Checking database consistency...")
        
        # Get all insights from MongoDB
        mongo_insights = await mongodb.read_many(
            "insights", {}, limit=1000
        )
        
        # Create a background task to process these in chunks to avoid 
        # blocking the main thread for too long
        asyncio.create_task(self._process_consistency_check(mongo_insights))
        
    async def _process_consistency_check(self, mongo_insights):
        """Process consistency check in background."""
        for insight in mongo_insights:
            insight_id = str(insight["_id"])
            
            # Check if insight exists in Neo4j graph by querying it
            with neo4j.driver.session() as session:
                result = session.run(
                    "MATCH (i:Insight {id: $id}) RETURN i.id",
                    id=insight_id
                )
                exists_in_neo4j = result.single() is not None
            
            # If insight doesn't exist in Neo4j, create it
            if not exists_in_neo4j:
                logger.info(f"Inconsistency detected: Insight {insight_id} missing in Neo4j")
                
                # Prepare properties for Neo4j
                neo4j_props = {
                    "title": insight.get("title", ""),
                    "tags": insight.get("tags", []),
                    "created_at": insight.get("created_at", ""),
                    "user_id": insight.get("user_id", "")
                }
                
                # Create node in Neo4j
                neo4j.create_insight_node(insight_id, neo4j_props)
        
        logger.info("Database consistency check completed")

    async def sync_insight(self, insight: Dict[str, Any], operation: str):
        """
        Synchronize insight between MongoDB and Neo4j.
        
        Args:
            insight: Insight document
            operation: One of "create", "update", "delete"
        """
        insight_id = str(insight.get("_id"))
        
        try:
            # Acquire lock to prevent concurrent modifications
            lock_value = await redis_client.acquire_lock(f"insight:{insight_id}")
            if not lock_value:
                logger.warning(f"Could not acquire lock for insight {insight_id}")
                return
                
            if operation == "create":
                # Create in Neo4j
                neo4j_props = {
                    "title": insight.get("title", ""),
                    "tags": insight.get("tags", []),
                    "created_at": insight.get("created_at", ""),
                    "user_id": insight.get("user_id", "")
                }
                neo4j.create_insight_node(insight_id, neo4j_props)
                
            elif operation == "update":
                # Update in Neo4j
                neo4j_props = {
                    "title": insight.get("title", ""),
                    "tags": insight.get("tags", [])
                }
                neo4j.update_insight_node(insight_id, neo4j_props)
                
                # Invalidate cache
                await redis_client.delete_cache(f"insight:{insight_id}")
                await redis_client.invalidate_pattern(f"insights:user:{insight.get('user_id', '')}:*")
                
            elif operation == "delete":
                # Delete from Neo4j
                neo4j.delete_insight_node(insight_id)
                
                # Invalidate cache
                await redis_client.delete_cache(f"insight:{insight_id}")
                await redis_client.invalidate_pattern(f"insights:user:{insight.get('user_id', '')}:*")
                await redis_client.invalidate_pattern(f"mindmap:{insight_id}:*")
                
        finally:
            # Release lock
            if lock_value:
                await redis_client.release_lock(f"insight:{insight_id}", lock_value)

    async def backup_mongodb_to_json(self, output_path: str):
        """
        Create a backup of MongoDB collections into JSON files.
        """
        collections = ["users", "insights"]
        for collection in collections:
            try:
                docs = await mongodb.read_many(collection, {}, limit=0)  # No limit
                with open(f"{output_path}/{collection}.json", "w") as f:
                    json.dump(docs, f)
                logger.info(f"Backup of {collection} completed")
            except Exception as e:
                logger.error(f"Backup error for {collection}: {e}")
                
    def backup_neo4j_to_cypher(self, output_path: str):
        """
        Create a backup of Neo4j database as Cypher commands.
        """
        try:
            with neo4j.driver.session() as session:
                # Get all nodes
                nodes_result = session.run("MATCH (n) RETURN n")
                nodes = [record["n"] for record in nodes_result]
                
                # Get all relationships
                rels_result = session.run("MATCH ()-[r]->() RETURN r")
                rels = [record["r"] for record in rels_result]
                
                # Write Cypher commands to recreate the graph
                with open(f"{output_path}/neo4j_backup.cypher", "w") as f:
                    # Write node creation commands
                    for node in nodes:
                        labels = ":".join(node.labels)
                        props = ", ".join([f"{k}: {repr(v)}" for k, v in node.items()])
                        f.write(f"CREATE (:{labels} {{{props}}});\n")
                    
                    # Write relationship creation commands
                    for rel in rels:
                        rel_type = rel.type
                        props = ", ".join([f"{k}: {repr(v)}" for k, v in rel.items()])
                        f.write(f"MATCH (a) WHERE a.id = '{rel.start_node['id']}'\n")
                        f.write(f"MATCH (b) WHERE b.id = '{rel.end_node['id']}'\n")
                        f.write(f"CREATE (a)-[:{rel_type} {{{props}}}]->(b);\n\n")
                        
                logger.info("Neo4j backup completed")
        except Exception as e:
            logger.error(f"Neo4j backup error: {e}")

# Create a singleton instance
db_manager = DatabaseManager()
