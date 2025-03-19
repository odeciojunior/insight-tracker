"""
Schema definition for Relationship collection.
"""

from ..schema_validation import SchemaRegistry, SCHEMA_TYPES, ASC

# Define the relationship schema according to JSON Schema specification
relationship_schema = {
    "bsonType": "object",
    "required": ["source_id", "target_id", "relationship_type", "created_at"],
    "properties": {
        "_id": {
            "bsonType": "objectId",
            "description": "The unique identifier for the relationship"
        },
        "source_id": {
            "bsonType": "objectId",
            "description": "Reference to the source insight"
        },
        "target_id": {
            "bsonType": "objectId",
            "description": "Reference to the target insight"
        },
        "relationship_type": {
            "bsonType": "string",
            "enum": ["similar", "parent_child", "sequential", "causal", "contradictory", "supports", "custom"],
            "description": "Type of relationship between insights"
        },
        "custom_type": {
            "bsonType": "string",
            "description": "Custom relationship type label if relationship_type is 'custom'"
        },
        "strength": {
            "bsonType": "double",
            "minimum": 0,
            "maximum": 1,
            "description": "Strength of the relationship, between 0 and 1"
        },
        "bidirectional": {
            "bsonType": "bool",
            "description": "Whether the relationship is bidirectional"
        },
        "user_defined": {
            "bsonType": "bool",
            "description": "Whether the relationship was defined by a user or detected by AI"
        },
        "metadata": {
            "bsonType": "object",
            "description": "Additional metadata for the relationship"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Timestamp of when the relationship was created"
        },
        "updated_at": {
            "bsonType": "date",
            "description": "Timestamp of when the relationship was last updated"
        }
    },
    "additionalProperties": False
}

# Register the schema with the registry
SchemaRegistry.register_schema("relationships", relationship_schema)

# Register indexes for the relationship collection
SchemaRegistry.register_index("relationships", [("source_id", ASC)])
SchemaRegistry.register_index("relationships", [("target_id", ASC)])
SchemaRegistry.register_index("relationships", [("source_id", ASC), ("target_id", ASC)], unique=True)
SchemaRegistry.register_index("relationships", [("relationship_type", ASC)])
