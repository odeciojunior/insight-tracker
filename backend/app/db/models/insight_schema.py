"""
Schema definition for Insight collection.
"""

from ..schema_validation import SchemaRegistry, SCHEMA_TYPES, ASC, DESC

# Define the insight schema according to JSON Schema specification
insight_schema = {
    "bsonType": "object",
    "required": ["title", "user_id", "created_at"],
    "properties": {
        "_id": {
            "bsonType": "objectId",
            "description": "The unique identifier for the insight"
        },
        "title": {
            "bsonType": "string",
            "minLength": 1,
            "maxLength": 200,
            "description": "Title of the insight"
        },
        "content": {
            "bsonType": "string",
            "description": "Content or description of the insight"
        },
        "summary": {
            "bsonType": "string",
            "description": "AI-generated summary of the insight"
        },
        "user_id": {
            "bsonType": "objectId",
            "description": "Reference to the user who created the insight"
        },
        "source_type": {
            "bsonType": "string",
            "enum": ["text", "audio", "image", "mixed"],
            "description": "Source type of the insight"
        },
        "is_private": {
            "bsonType": "bool",
            "description": "Whether the insight is private to the user"
        },
        "tags": {
            "bsonType": "array",
            "items": {
                "bsonType": "string"
            },
            "description": "Tags associated with the insight"
        },
        "categories": {
            "bsonType": "array",
            "items": {
                "bsonType": "string"
            },
            "description": "Categories the insight belongs to"
        },
        "embeddings": {
            "bsonType": "array",
            "items": {
                "bsonType": "double"
            },
            "description": "Vector embeddings of the insight for semantic search"
        },
        "metadata": {
            "bsonType": "object",
            "description": "Additional metadata for the insight"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Timestamp of when the insight was created"
        },
        "updated_at": {
            "bsonType": "date",
            "description": "Timestamp of when the insight was last updated"
        }
    },
    "additionalProperties": False
}

# Register the schema with the registry
SchemaRegistry.register_schema("insights", insight_schema)

# Register indexes for the insight collection
SchemaRegistry.register_index("insights", [("user_id", ASC), ("created_at", DESC)])
SchemaRegistry.register_index("insights", [("tags", ASC)])
SchemaRegistry.register_index("insights", [("categories", ASC)])
SchemaRegistry.register_index("insights", [("created_at", DESC)])
