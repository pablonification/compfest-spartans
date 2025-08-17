from __future__ import annotations

from typing import List, Optional

from ..db.mongo import get_database
from ..models.educational import EducationalContent
from bson import ObjectId


class EducationalService:
    """Service for CRUD operations on educational content."""

    def __init__(self):
        self.db = get_database()
        self.collection = self.db.educational_contents

    async def create(self, data: dict) -> EducationalContent:
        payload = EducationalContent(**data)
        result = await self.collection.insert_one(payload.model_dump(by_alias=True, exclude={"id"}))
        payload.id = str(result.inserted_id)
        return payload

    async def list(self, limit: int = 50, skip: int = 0) -> list[EducationalContent]:
        cursor = (
            self.collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        )
        items: List[EducationalContent] = []
        async for doc in cursor:
            items.append(EducationalContent.model_validate(doc))
        return items

    async def get(self, content_id: str | ObjectId) -> Optional[EducationalContent]:
        if isinstance(content_id, str):
            content_id = ObjectId(content_id)
        doc = await self.collection.find_one({"_id": content_id})
        if doc:
            return EducationalContent.model_validate(doc)
        return None

    async def update(self, content_id: str | ObjectId, data: dict) -> Optional[EducationalContent]:
        if isinstance(content_id, str):
            content_id = ObjectId(content_id)
        await self.collection.update_one({"_id": content_id}, {"$set": data})
        return await self.get(content_id)

    async def delete(self, content_id: str | ObjectId) -> bool:
        if isinstance(content_id, str):
            content_id = ObjectId(content_id)
        result = await self.collection.delete_one({"_id": content_id})
        return result.deleted_count == 1
