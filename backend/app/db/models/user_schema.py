"""
Schema definition for User collection.
"""

from ..schema_validation import SchemaRegistry, SCHEMA_TYPES, ASC

# Define the user schema according to JSON Schema specification
user_schema = {
    "bsonType": "object",
    "required": ["email", "username", "password_hash", "created_at"],
    "properties": {
        "_id": {
            "bsonType": "objectId",
            "description": "The unique identifier for the user"
        },
        "email": {
            "bsonType": "string",
            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            "description": "User's email address"
        },
        "username": {
            "bsonType": "string",
            "minLength": 3,
            "maxLength": 50,
            "description": "User's chosen username"
        },
        "password_hash": {
            "bsonType": "string",
            "description": "Hashed password"
        },
        "full_name": {
            "bsonType": "string",
            "description": "User's full name"
        },
        "profile_image": {
            "bsonType": "string",
            "description": "URL to user's profile image"
        },
        "bio": {
            "bsonType": "string",
            "maxLength": 500,
            "description": "User's biographical information"
        },
        "preferences": {
            "bsonType": "object",
            "description": "User preferences and settings"
        },
        "is_active": {
            "bsonType": "bool",
            "description": "Whether the user account is active"
        },
        "is_admin": {
            "bsonType": "bool",
            "description": "Whether the user has admin privileges"
        },
        "last_login": {
            "bsonType": "date",
            "description": "Timestamp of the user's last login"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Timestamp of when the user was created"
        },
        "updated_at": {
            "bsonType": "date",
            "description": "Timestamp of when the user was last updated"
        }
    },
    "additionalProperties": False
}

# Register the schema with the registry
SchemaRegistry.register_schema("users", user_schema)

# Register indexes for the user collection
SchemaRegistry.register_index("users", [("email", ASC)], unique=True)
SchemaRegistry.register_index("users", [("username", ASC)], unique=True)
SchemaRegistry.register_index("users", [("created_at", ASC)])
