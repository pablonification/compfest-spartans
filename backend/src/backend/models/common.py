from __future__ import annotations

from bson import ObjectId  # type: ignore
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from pydantic_core import core_schema
from typing import Any


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler) -> core_schema.CoreSchema:
        """Get Pydantic core schema for validation."""
        return core_schema.with_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v: Any) -> "PyObjectId":
        """Validate and convert value to ObjectId."""
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)


class MongoBaseModel(BaseModel):
    """Base model that serializes ObjectId to str for JSON."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    model_config = ConfigDict(
        validate_by_name=True,  # renamed from allow_population_by_field_name
        populate_by_name=True    # alternative approach for V2
    )
    
    @field_serializer('id')
    def serialize_id(self, id: PyObjectId) -> str:
        """Serialize ObjectId to string for JSON output."""
        return str(id)
