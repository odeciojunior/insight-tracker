"""
MongoDB schema definitions for the Insight Tracker application.
"""

from ..schema_validation import SchemaRegistry

# Import all schemas to register them
from . import user_schema
from . import insight_schema
from . import relationship_schema

# Function to initialize all schemas and indexes
async def init_db_schemas():
    """
    Initialize all database schemas and indexes.
    
    This function applies all registered schema validations and indexes to their
    respective MongoDB collections. It should be called during application startup.
    """
    await SchemaRegistry.apply_all_schemas()
    await SchemaRegistry.apply_all_indexes()
