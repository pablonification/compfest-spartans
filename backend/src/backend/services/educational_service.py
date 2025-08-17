from __future__ import annotations

from typing import List, Optional

from ..db.mongo import get_database
from ..models.educational import EducationalContent
from bson import ObjectId


class EducationalService:
    """Service for CRUD operations on educational content."""

    def __init__(self):
        pass

    def _get_collection(self):
        db = get_database()
        return db.educational_contents

    async def create(self, data: dict) -> EducationalContent:
        payload = EducationalContent(**data)
        collection = self._get_collection()
        result = await collection.insert_one(payload.model_dump(by_alias=True, exclude={"id"}))
        payload.id = str(result.inserted_id)
        return payload

    async def list(self, limit: int = 50, skip: int = 0) -> list[EducationalContent]:
        collection = self._get_collection()
        cursor = (
            collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        )
        items: List[EducationalContent] = []
        async for doc in cursor:
            items.append(EducationalContent.model_validate(doc))
        return items

    async def get(self, content_id: str | ObjectId) -> Optional[EducationalContent]:
        if isinstance(content_id, str):
            content_id = ObjectId(content_id)
        collection = self._get_collection()
        doc = await collection.find_one({"_id": content_id})
        if doc:
            return EducationalContent.model_validate(doc)
        return None

    async def update(self, content_id: str | ObjectId, data: dict) -> Optional[EducationalContent]:
        if isinstance(content_id, str):
            content_id = ObjectId(content_id)
        collection = self._get_collection()
        await collection.update_one({"_id": content_id}, {"$set": data})
        return await self.get(content_id)

    async def delete(self, content_id: str | ObjectId) -> bool:
        if isinstance(content_id, str):
            content_id = ObjectId(content_id)
        collection = self._get_collection()
        result = await collection.delete_one({"_id": content_id})
        return result.deleted_count == 1
