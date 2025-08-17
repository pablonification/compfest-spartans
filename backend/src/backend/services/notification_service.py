from __future__ import annotations

from datetime import datetime
from typing import List, Optional
import asyncio
from bson import ObjectId

from ..models.notification import Notification, NotificationSettings
from ..db.mongo import get_database


class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self):
        pass
    
    def _get_collections(self):
        db = get_database()
        return db.notifications, db.notification_settings
    
    async def create_notification(
        self,
        user_id: str | ObjectId,
        title: str,
        message: str,
        notification_type: str = "system",
        priority: int = 2,
        **kwargs
    ) -> Notification:
        """Create a new notification."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        notification_data = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "priority": priority,
            **kwargs
        }
        
        notification = Notification(**notification_data)
        
        # Insert into database
        notifications_collection, _ = self._get_collections()
        result = await notifications_collection.insert_one(notification.model_dump(by_alias=True))
        notification.id = result.inserted_id
        
        return notification
    
    async def create_bin_status_notification(
        self,
        user_id: str | ObjectId,
        bin_id: str,
        bin_status: str,
        message: str
    ) -> Notification:
        """Create a bin status notification."""
        title_map = {
            "full": "Tong Sampah Penuh",
            "maintenance": "Tong Sampah Dalam Perawatan",
            "available": "Tong Sampah Tersedia"
        }
        
        title = title_map.get(bin_status, "Update Status Tong Sampah")
        
        return await self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="bin_status",
            bin_id=bin_id,
            bin_status=bin_status,
            priority=3 if bin_status == "full" else 2
        )
    
    async def create_achievement_notification(
        self,
        user_id: str | ObjectId,
        achievement_type: str,
        achievement_value: int,
        message: str
    ) -> Notification:
        """Create an achievement notification."""
        title = f"Pencapaian Baru: {achievement_type}"
        
        return await self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="achievement",
            achievement_type=achievement_type,
            achievement_value=achievement_value,
            priority=2
        )
    
    async def create_reward_notification(
        self,
        user_id: str | ObjectId,
        points: int,
        bottle_count: int = 1
    ) -> Notification:
        """Create a reward notification."""
        title = "Reward Diterima!"
        message = f"Selamat! Anda mendapatkan {points} poin untuk {bottle_count} botol yang dibuang."
        
        return await self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="reward",
            priority=1
        )
    
    async def get_user_notifications(
        self,
        user_id: str | ObjectId,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a specific user."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        filter_query = {"user_id": user_id}
        if unread_only:
            filter_query["is_read"] = False
        
        # Execute query (supports both sync cursor and awaited cursor in tests)
        notifications_collection, _ = self._get_collections()
        result = notifications_collection.find(filter_query)
        if asyncio.iscoroutine(result):
            result = await result
        cursor = result.sort("created_at", -1).limit(limit)
        # Some mocks may return plain list instead of cursor
        if hasattr(cursor, "__aiter__"):
            return [Notification(**doc) async for doc in cursor]
        else:
            return [Notification(**doc) for doc in cursor]
    
    async def mark_as_read(
        self,
        notification_id: str | ObjectId,
        user_id: str | ObjectId
    ) -> bool:
        """Mark a notification as read."""
        if isinstance(notification_id, str):
            notification_id = ObjectId(notification_id)
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        notifications_collection, _ = self._get_collections()
        result = await notifications_collection.update_one(
            {"_id": notification_id, "user_id": user_id},
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def mark_all_as_read(
        self,
        user_id: str | ObjectId
    ) -> int:
        """Mark all notifications as read for a user."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        notifications_collection, _ = self._get_collections()
        result = await notifications_collection.update_many(
            {"user_id": user_id, "is_read": False},
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count
    
    async def delete_notification(
        self,
        notification_id: str | ObjectId,
        user_id: str | ObjectId
    ) -> bool:
        """Delete a notification."""
        if isinstance(notification_id, str):
            notification_id = ObjectId(notification_id)
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        notifications_collection, _ = self._get_collections()
        result = await notifications_collection.delete_one({
            "_id": notification_id,
            "user_id": user_id
        })
        
        return result.deleted_count > 0
    
    async def get_unread_count(self, user_id: str | ObjectId) -> int:
        """Get count of unread notifications for a user."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        notifications_collection, _ = self._get_collections()
        return await notifications_collection.count_documents({
            "user_id": user_id,
            "is_read": False
        })
    
    async def get_or_create_settings(self, user_id: str | ObjectId) -> NotificationSettings:
        """Get or create notification settings for a user."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        _, settings_collection = self._get_collections()
        settings = await settings_collection.find_one({"user_id": user_id})
        
        if not settings:
            # Create default settings
            default_settings = NotificationSettings(user_id=user_id)
            result = await settings_collection.insert_one(
                default_settings.model_dump(by_alias=True)
            )
            default_settings.id = result.inserted_id
            return default_settings
        
        return NotificationSettings(**settings)
    
    async def update_settings(
        self,
        user_id: str | ObjectId,
        **kwargs
    ) -> NotificationSettings:
        """Update notification settings for a user."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        # Remove None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        _, settings_collection = self._get_collections()
        result = await settings_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        modified = getattr(result, "modified_count", 0)
        if hasattr(modified, "__call__"):
            modified = modified()
        if modified > 0:
            return await self.get_or_create_settings(user_id)
        return await self.get_or_create_settings(user_id)


# Global instance - lazy initialization
_notification_service = None

def get_notification_service():
    """Get or create notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
