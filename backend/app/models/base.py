from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class BaseDBModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        
    def dict_for_db(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage."""
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data

class MongoBaseModel(BaseDBModel):
    """Base model for MongoDB documents."""
    
    @classmethod
    async def get_collection_name(cls) -> str:
        """Get the collection name for this model."""
        return cls.__name__.lower() + 's'
    
    async def save(self):
        """Save the model to MongoDB."""
        from ..db.mongodb import get_mongodb
        
        db = await get_mongodb()
        collection = db[await self.get_collection_name()]
        
        data = self.dict_for_db()
        if not self.id:
            # Insert new document
            result = await collection.insert_one(data)
            self.id = result.inserted_id
        else:
            # Update existing document
            await collection.update_one(
                {"_id": self.id},
                {"$set": data}
            )
        return self

class Neo4jBaseModel(BaseDBModel):
    """Base model for Neo4j nodes."""
    
    def to_node_properties(self) -> Dict[str, Any]:
        """Convert model to Neo4j node properties."""
        data = self.dict(exclude={"id"})
        if isinstance(self.id, ObjectId):
            data["mongo_id"] = str(self.id)
        return data

    @classmethod
    async def get_node_label(cls) -> str:
        """Get the Neo4j node label for this model."""
        return cls.__name__
