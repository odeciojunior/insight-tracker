"""
MongoDB schema validation module.

This module provides functionality to create and apply JSON Schema validation 
rules for MongoDB collections, ensuring data integrity.
"""

import logging
from typing import Dict, Any, List, Optional
from pymongo import ASCENDING, DESCENDING
from .mongodb import get_mongodb

logger = logging.getLogger(__name__)

class SchemaRegistry:
    """
    Registry for schema validation rules for MongoDB collections.
    
    Maintains a central repository of schema validation rules and provides
    methods to apply these rules to MongoDB collections.
    """
    
    # Registry of schemas by collection name
    _schemas: Dict[str, Dict[str, Any]] = {}
    
    # Registry of indexes by collection name
    _indexes: Dict[str, List[Dict[str, Any]]] = {}
    
    @classmethod
    def register_schema(cls, collection_name: str, schema: Dict[str, Any]) -> None:
        """
        Register a schema validation rule for a collection.
        
        Args:
            collection_name: Name of the collection
            schema: JSON Schema definition for validation
        """
        cls._schemas[collection_name] = schema
        logger.info(f"Schema registered for collection '{collection_name}'")
    
    @classmethod
    def register_index(cls, collection_name: str, keys: List[tuple], unique: bool = False, 
                      sparse: bool = False, expireAfterSeconds: Optional[int] = None, 
                      name: Optional[str] = None) -> None:
        """
        Register an index configuration for a collection.
        
        Args:
            collection_name: Name of the collection
            keys: List of (field, direction) tuples, where direction is 
                  pymongo.ASCENDING or pymongo.DESCENDING
            unique: Whether the index should enforce uniqueness
            sparse: Whether the index should be sparse
            expireAfterSeconds: TTL for documents (for TTL indexes)
            name: Optional custom name for the index
        """
        if collection_name not in cls._indexes:
            cls._indexes[collection_name] = []
        
        index_config = {
            "keys": keys,
            "unique": unique,
            "sparse": sparse
        }
        
        if expireAfterSeconds is not None:
            index_config["expireAfterSeconds"] = expireAfterSeconds
            
        if name:
            index_config["name"] = name
            
        cls._indexes[collection_name].append(index_config)
        logger.info(f"Index registered for collection '{collection_name}': {keys}")
    
    @classmethod
    def get_schema(cls, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the registered schema for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Optional[Dict[str, Any]]: The schema or None if not registered
        """
        return cls._schemas.get(collection_name)
    
    @classmethod
    def get_indexes(cls, collection_name: str) -> List[Dict[str, Any]]:
        """
        Get the registered indexes for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            List[Dict[str, Any]]: List of index configurations
        """
        return cls._indexes.get(collection_name, [])
    
    @classmethod
    async def apply_schema_validation(cls, collection_name: str, validation_level: str = "strict", 
                                    validation_action: str = "error") -> None:
        """
        Apply the registered schema validation to a MongoDB collection.
        
        Args:
            collection_name: Name of the collection
            validation_level: MongoDB validation level ('off', 'strict', or 'moderate')
            validation_action: Action to take when validation fails ('error' or 'warn')
        """
        schema = cls.get_schema(collection_name)
        if not schema:
            logger.warning(f"No schema registered for collection '{collection_name}'")
            return
            
        mongodb = await get_mongodb()
        
        # Create validator command
        validator_cmd = {
            "validator": {"$jsonSchema": schema},
            "validationLevel": validation_level,
            "validationAction": validation_action
        }
        
        try:
            # Apply the validator to the collection
            await mongodb._client.admin.command(
                "collMod", 
                collection_name,
                **validator_cmd
            )
            logger.info(f"Applied schema validation to collection '{collection_name}'")
        except Exception as e:
            # Collection may not exist yet, create it with validation
            try:
                await mongodb._client[mongodb._db_name].create_collection(
                    collection_name,
                    **validator_cmd
                )
                logger.info(f"Created collection '{collection_name}' with schema validation")
            except Exception as create_e:
                logger.error(f"Failed to apply schema validation to '{collection_name}': {str(create_e)}")
                raise
    
    @classmethod
    async def apply_indexes(cls, collection_name: str) -> List[str]:
        """
        Apply the registered indexes to a MongoDB collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            List[str]: List of created index names
        """
        indexes = cls.get_indexes(collection_name)
        if not indexes:
            logger.warning(f"No indexes registered for collection '{collection_name}'")
            return []
            
        mongodb = await get_mongodb()
        created_indexes = []
        
        for index_config in indexes:
            try:
                keys = index_config.pop("keys")
                
                # Create the index
                index_name = await mongodb.create_index(
                    collection_name, 
                    keys,
                    **index_config
                )
                
                created_indexes.append(index_name)
                logger.info(f"Created index '{index_name}' on collection '{collection_name}'")
            except Exception as e:
                logger.error(f"Failed to create index on '{collection_name}': {str(e)}")
        
        return created_indexes
    
    @classmethod
    async def apply_all_schemas(cls) -> None:
        """
        Apply all registered schema validations to their respective collections.
        """
        for collection_name in cls._schemas.keys():
            await cls.apply_schema_validation(collection_name)
    
    @classmethod
    async def apply_all_indexes(cls) -> Dict[str, List[str]]:
        """
        Apply all registered indexes to their respective collections.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping collection names to lists of created index names
        """
        result = {}
        for collection_name in cls._indexes.keys():
            created_indexes = await cls.apply_indexes(collection_name)
            result[collection_name] = created_indexes
        return result

    @staticmethod
    def get_user_schema() -> Dict[str, Any]:
        return {
            "bsonType": "object",
            "required": ["email", "username", "hashed_password"],
            "properties": {
                "email": {
                    "bsonType": "string",
                    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                },
                "username": {
                    "bsonType": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "hashed_password": {
                    "bsonType": "string"
                },
                "is_active": {
                    "bsonType": "bool"
                },
                "created_at": {
                    "bsonType": "date"
                }
            }
        }
    
    @staticmethod
    def get_insight_schema() -> Dict[str, Any]:
        return {
            "bsonType": "object",
            "required": ["user_id", "title", "content", "created_at"],
            "properties": {
                "user_id": {
                    "bsonType": "objectId"
                },
                "title": {
                    "bsonType": "string",
                    "minLength": 1,
                    "maxLength": 200
                },
                "content": {
                    "bsonType": "string"
                },
                "tags": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "string"
                    }
                },
                "embedding": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "double"
                    }
                },
                "source_type": {
                    "bsonType": "string",
                    "enum": ["text", "audio", "image"]
                },
                "created_at": {
                    "bsonType": "date"
                },
                "updated_at": {
                    "bsonType": "date"
                }
            }
        }

    @staticmethod
    def get_relationship_schema() -> Dict[str, Any]:
        return {
            "bsonType": "object",
            "required": ["source_id", "target_id", "type", "created_at"],
            "properties": {
                "source_id": {
                    "bsonType": "objectId"
                },
                "target_id": {
                    "bsonType": "objectId"
                },
                "type": {
                    "bsonType": "string"
                },
                "strength": {
                    "bsonType": "double",
                    "minimum": 0,
                    "maximum": 1
                },
                "metadata": {
                    "bsonType": "object"
                },
                "created_at": {
                    "bsonType": "date"
                }
            }
        }

    @staticmethod
    def get_indexes() -> Dict[str, list]:
        return {
            "users": [
                [("email", ASC)],
                [("username", ASC)],
                [("created_at", DESC)]
            ],
            "insights": [
                [("user_id", ASC)],
                [("created_at", DESC)],
                [("tags", ASC)],
                [("title", "text"), ("content", "text")]
            ],
            "relationships": [
                [("source_id", ASC)],
                [("target_id", ASC)],
                [("type", ASC)],
                [("created_at", DESC)]
            ]
        }

# Define common schema types for reuse in validation schemas
SCHEMA_TYPES = {
    "string": {"type": "string"},
    "objectId": {"type": "string", "pattern": "^[0-9a-fA-F]{24}$"},
    "email": {
        "type": "string", 
        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    },
    "date": {"bsonType": "date"},
    "array": {"type": "array"},
    "number": {"type": "number"},
    "integer": {"type": "integer"},
    "boolean": {"type": "boolean"},
    "object": {"type": "object"},
    "timestamp": {"bsonType": "timestamp"},
}

# Index direction constants for convenience
ASC = ASCENDING
DESC = DESCENDING
