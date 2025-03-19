import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError
from bson import ObjectId

# Configure logging
logger = logging.getLogger(__name__)

class MongoDBClient:
    """
    Asynchronous MongoDB client with retry mechanism and health check.
    
    This class provides a wrapper around Motor for asynchronous MongoDB operations
    with built-in retry logic for resilience and utility functions for common operations.
    """
    
    def __init__(
        self, 
        connection_string: str, 
        db_name: str,
        max_pool_size: int = 10,
        min_pool_size: int = 1,
        max_retry_attempts: int = 3,
        retry_delay: float = 0.5
    ):
        """
        Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection URI
            db_name: Database name to connect to
            max_pool_size: Maximum number of connections in the pool
            min_pool_size: Minimum number of connections in the pool
            max_retry_attempts: Maximum number of retry attempts on failed operations
            retry_delay: Delay between retry attempts in seconds
        """
        self._connection_string = connection_string
        self._db_name = db_name
        self._max_pool_size = max_pool_size
        self._min_pool_size = min_pool_size
        self._max_retry_attempts = max_retry_attempts
        self._retry_delay = retry_delay
        
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """
        Establish connection to MongoDB with retry mechanism.
        """
        for attempt in range(1, self._max_retry_attempts + 1):
            try:
                logger.info(f"Connecting to MongoDB (attempt {attempt}/{self._max_retry_attempts})...")
                self._client = AsyncIOMotorClient(
                    self._connection_string,
                    maxPoolSize=self._max_pool_size,
                    minPoolSize=self._min_pool_size,
                    serverSelectionTimeoutMS=5000
                )
                
                # Force a connection to verify it's working
                await self._client.admin.command("ping")
                
                self._db = self._client[self._db_name]
                logger.info(f"Successfully connected to MongoDB database '{self._db_name}'")
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"Failed to connect to MongoDB (attempt {attempt}/{self._max_retry_attempts}): {str(e)}")
                
                if attempt < self._max_retry_attempts:
                    wait_time = self._retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.critical("Could not establish connection to MongoDB after multiple attempts")
                    raise
    
    async def close(self) -> None:
        """
        Close MongoDB connection.
        """
        if self._client:
            logger.info("Closing MongoDB connection...")
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed successfully")
    
    async def check_health(self) -> bool:
        """
        Check if the MongoDB connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self._client:
            logger.warning("Health check failed: No MongoDB client available")
            return False
        
        try:
            # Try to execute a simple command to check the connection
            await self._client.admin.command("ping")
            logger.debug("MongoDB health check: Connection is healthy")
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            return False
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """
        Get a reference to a MongoDB collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            AsyncIOMotorCollection: The requested collection
        """
        if not self._db:
            raise ConnectionError("MongoDB client is not connected")
            
        return self._db[collection_name]
    
    async def create_index(self, collection_name: str, keys: List, **kwargs) -> str:
        """
        Create an index on a collection.
        
        Args:
            collection_name: Name of the collection
            keys: List of (key, direction) pairs
            **kwargs: Additional arguments to pass to create_index
            
        Returns:
            str: Name of the created index
        """
        collection = self.get_collection(collection_name)
        return await collection.create_index(keys, **kwargs)
    
    async def _execute_with_retry(self, operation, *args, **kwargs):
        """
        Execute a MongoDB operation with retry logic.
        
        Args:
            operation: Async function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            The result of the operation
        """
        for attempt in range(1, self._max_retry_attempts + 1):
            try:
                return await operation(*args, **kwargs)
            except (ConnectionFailure, OperationFailure) as e:
                logger.warning(f"Operation failed (attempt {attempt}/{self._max_retry_attempts}): {str(e)}")
                
                if attempt < self._max_retry_attempts:
                    wait_time = self._retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying operation in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Operation failed after maximum retry attempts")
                    raise
    
    # CRUD utility functions
    
    async def find_one(self, collection_name: str, query: Dict, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Find a single document in the collection.
        
        Args:
            collection_name: Name of the collection
            query: Query to filter documents
            *args, **kwargs: Additional arguments to pass to find_one
            
        Returns:
            Optional[Dict[str, Any]]: Found document or None
        """
        collection = self.get_collection(collection_name)
        return await self._execute_with_retry(collection.find_one, query, *args, **kwargs)
    
    async def find_many(
        self, 
        collection_name: str, 
        query: Dict, 
        skip: int = 0, 
        limit: int = 0, 
        sort=None, 
        *args, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents in the collection.
        
        Args:
            collection_name: Name of the collection
            query: Query to filter documents
            skip: Number of documents to skip
            limit: Maximum number of documents to return (0 for no limit)
            sort: Sorting specification
            *args, **kwargs: Additional arguments to pass to find
            
        Returns:
            List[Dict[str, Any]]: List of found documents
        """
        collection = self.get_collection(collection_name)
        cursor = collection.find(query, *args, **kwargs)
        
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort:
            cursor = cursor.sort(sort)
            
        return await self._execute_with_retry(cursor.to_list, length=None)
    
    async def insert_one(self, collection_name: str, document: Dict, *args, **kwargs) -> str:
        """
        Insert a single document into the collection.
        
        Args:
            collection_name: Name of the collection
            document: Document to insert
            *args, **kwargs: Additional arguments to pass to insert_one
            
        Returns:
            str: ID of the inserted document
        """
        collection = self.get_collection(collection_name)
        result = await self._execute_with_retry(collection.insert_one, document, *args, **kwargs)
        return str(result.inserted_id)
    
    async def insert_many(self, collection_name: str, documents: List[Dict], *args, **kwargs) -> List[str]:
        """
        Insert multiple documents into the collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of documents to insert
            *args, **kwargs: Additional arguments to pass to insert_many
            
        Returns:
            List[str]: IDs of inserted documents
        """
        collection = self.get_collection(collection_name)
        result = await self._execute_with_retry(collection.insert_many, documents, *args, **kwargs)
        return [str(id) for id in result.inserted_ids]
    
    async def update_one(
        self, 
        collection_name: str, 
        query: Dict, 
        update: Dict, 
        upsert: bool = False, 
        *args, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update a single document in the collection.
        
        Args:
            collection_name: Name of the collection
            query: Query to filter documents
            update: Update operations
            upsert: Whether to insert if document doesn't exist
            *args, **kwargs: Additional arguments to pass to update_one
            
        Returns:
            Dict[str, Any]: Update result containing matched_count and modified_count
        """
        collection = self.get_collection(collection_name)
        result = await self._execute_with_retry(
            collection.update_one, 
            query, 
            update, 
            upsert=upsert, 
            *args, 
            **kwargs
        )
        
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None
        }
    
    async def update_many(
        self, 
        collection_name: str, 
        query: Dict, 
        update: Dict, 
        *args, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update multiple documents in the collection.
        
        Args:
            collection_name: Name of the collection
            query: Query to filter documents
            update: Update operations
            *args, **kwargs: Additional arguments to pass to update_many
            
        Returns:
            Dict[str, Any]: Update result containing matched_count and modified_count
        """
        collection = self.get_collection(collection_name)
        result = await self._execute_with_retry(
            collection.update_many, 
            query, 
            update, 
            *args, 
            **kwargs
        )
        
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        }
    
    async def delete_one(self, collection_name: str, query: Dict, *args, **kwargs) -> int:
        """
        Delete a single document from the collection.
        
        Args:
            collection_name: Name of the collection
            query: Query to filter documents
            *args, **kwargs: Additional arguments to pass to delete_one
            
        Returns:
            int: Number of documents deleted
        """
        collection = self.get_collection(collection_name)
        result = await self._execute_with_retry(collection.delete_one, query, *args, **kwargs)
        return result.deleted_count
    
    async def delete_many(self, collection_name: str, query: Dict, *args, **kwargs) -> int:
        """
        Delete multiple documents from the collection.
        
        Args:
            collection_name: Name of the collection
            query: Query to filter documents
            *args, **kwargs: Additional arguments to pass to delete_many
            
        Returns:
            int: Number of documents deleted
        """
        collection = self.get_collection(collection_name)
        result = await self._execute_with_retry(collection.delete_many, query, *args, **kwargs)
        return result.deleted_count
    
    async def count_documents(self, collection_name: str, query: Dict, *args, **kwargs) -> int:
        """
        Count documents in the collection.
        
        Args:
            collection_name: Name of the collection
            query: Query to filter documents
            *args, **kwargs: Additional arguments to pass to count_documents
            
        Returns:
            int: Number of documents matching the query
        """
        collection = self.get_collection(collection_name)
        return await self._execute_with_retry(collection.count_documents, query, *args, **kwargs)
    
    async def aggregate(self, collection_name: str, pipeline: List[Dict], *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform an aggregation pipeline on the collection.
        
        Args:
            collection_name: Name of the collection
            pipeline: List of aggregation pipeline stages
            *args, **kwargs: Additional arguments to pass to aggregate
            
        Returns:
            List[Dict[str, Any]]: Result of the aggregation
        """
        collection = self.get_collection(collection_name)
        cursor = collection.aggregate(pipeline, *args, **kwargs)
        return await self._execute_with_retry(cursor.to_list, length=None)

# Singleton instance of the MongoDB client
mongodb_client: Optional[MongoDBClient] = None

async def init_mongodb(
    connection_string: str,
    db_name: str,
    max_pool_size: int = 10,
    min_pool_size: int = 1,
    max_retry_attempts: int = 3,
    retry_delay: float = 0.5
) -> MongoDBClient:
    """
    Initialize the MongoDB client singleton.
    
    Args:
        connection_string: MongoDB connection URI
        db_name: Database name to connect to
        max_pool_size: Maximum number of connections in the pool
        min_pool_size: Minimum number of connections in the pool
        max_retry_attempts: Maximum number of retry attempts on failed operations
        retry_delay: Delay between retry attempts in seconds
        
    Returns:
        MongoDBClient: The initialized MongoDB client instance
    """
    global mongodb_client
    
    if mongodb_client is None:
        mongodb_client = MongoDBClient(
            connection_string=connection_string,
            db_name=db_name,
            max_pool_size=max_pool_size,
            min_pool_size=min_pool_size,
            max_retry_attempts=max_retry_attempts,
            retry_delay=retry_delay
        )
        await mongodb_client.connect()
    
    return mongodb_client

async def close_mongodb() -> None:
    """
    Close the MongoDB client connection.
    """
    global mongodb_client
    if mongodb_client:
        await mongodb_client.close()
        mongodb_client = None

async def get_mongodb() -> MongoDBClient:
    """
    Get the MongoDB client instance.
    
    Returns:
        MongoDBClient: The MongoDB client instance
    
    Raises:
        ConnectionError: If the MongoDB client has not been initialized
    """
    if mongodb_client is None:
        raise ConnectionError("MongoDB client has not been initialized. Call init_mongodb first.")
    
    return mongodb_client

# Helper function to convert string IDs to ObjectId
def convert_id(id: str) -> ObjectId:
    """Convert string ID to ObjectId."""
    return ObjectId(id)
