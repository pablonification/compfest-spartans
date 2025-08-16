from __future__ import annotations

from bson import ObjectId  # type: ignore
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""

    @classmethod
    def __get_validators__(cls):  # noqa: D401
        yield cls.validate

    @classmethod
    def validate(cls, v):  # noqa: ANN001, D401, N805
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)


class MongoBaseModel(BaseModel):
    """Base model that serializes ObjectId to str for JSON."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
