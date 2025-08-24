import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import AsyncMock, patch, MagicMock

from backend.models.notification import Notification, NotificationSettings
from backend.services.notification_service import NotificationService
from backend.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationSettingsUpdate
)


class TestNotificationModels:
    """Test notification models."""
    
    def test_notification_creation(self):
        """Test creating a notification."""
        notification = Notification(
            user_id=ObjectId(),
            title="Test Notification",
            message="This is a test notification",
            notification_type="system",
            priority=2
        )
        
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.notification_type == "system"
        assert notification.priority == 2
        assert notification.is_read is False
        assert notification.created_at is not None
    
    def test_notification_with_bin_status(self):
        """Test creating a bin status notification."""
        notification = Notification(
            user_id=ObjectId(),
            title="Bin Full",
            message="The bin is full",
            notification_type="bin_status",
            bin_id="bin_001",
            bin_status="full",
            priority=3
        )
        
        assert notification.bin_id == "bin_001"
        assert notification.bin_status == "full"
        assert notification.priority == 3
    
    def test_notification_with_achievement(self):
        """Test creating an achievement notification."""
        notification = Notification(
            user_id=ObjectId(),
            title="Achievement Unlocked",
            message="You've earned a new achievement",
            notification_type="achievement",
            achievement_type="First Bottle",
            achievement_value=1,
            priority=2
        )
        
        assert notification.achievement_type == "First Bottle"
        assert notification.achievement_value == 1
    
    def test_notification_settings_creation(self):
        """Test creating notification settings."""
        settings = NotificationSettings(
            user_id=ObjectId(),
            email_notifications=True,
            push_notifications=False,
            bin_status_notifications=True,
            achievement_notifications=False,
            system_notifications=True,
            reward_notifications=True,
            quiet_hours_start=22,
            quiet_hours_end=7
        )
        
        assert settings.email_notifications is True
        assert settings.push_notifications is False
        assert settings.quiet_hours_start == 22
        assert settings.quiet_hours_end == 7


class TestNotificationService:
    """Test notification service."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database with async collections and methods."""
        def _make_collection():
            from types import SimpleNamespace
            from bson import ObjectId
            # helper cursor
            async def _empty_async_iter():
                if False:
                    yield None
            class _Cursor:
                def __init__(self, data=None):
                    self._data = data or []
                def sort(self, *_args, **_kwargs):
                    return self
                def limit(self, *_args, **_kwargs):
                    return self
                def __aiter__(self):
                    return iter(self._data)
            col = MagicMock()
            # async compatible methods
            async def _insert_one(doc):
                return SimpleNamespace(inserted_id=ObjectId())
            async def _update_one(*_a, **_k):
                return SimpleNamespace(modified_count=1)
            async def _update_many(*_a, **_k):
                return SimpleNamespace(modified_count=1)
            async def _delete_one(*_a, **_k):
                return SimpleNamespace(deleted_count=1)
            async def _count_documents(*_a, **_k):
                return 0
            async def _find_one(*_a, **_k):
                return None
            async def _find(filter_query):
                return _Cursor()
            col.insert_one = AsyncMock(side_effect=_insert_one)
            col.update_one = AsyncMock(side_effect=_update_one)
            col.update_many = AsyncMock(side_effect=_update_many)
            col.delete_one = AsyncMock(side_effect=_delete_one)
            col.count_documents = AsyncMock(side_effect=_count_documents)
            col.find_one = AsyncMock(side_effect=_find_one)
            col.find = AsyncMock(side_effect=_find)
            return col

        mock_db = MagicMock()
        mock_db.notifications = _make_collection()
        mock_db.notification_settings = _make_collection()
        return mock_db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service with mocked database."""
        with patch('backend.services.notification_service.get_database', return_value=mock_db):
            return NotificationService()
    
    @pytest.mark.asyncio
    async def test_create_notification(self, service, mock_db):
        """Test creating a notification."""
        user_id = ObjectId()
        mock_db.notifications.insert_one.return_value.inserted_id = ObjectId()
        
        notification = await service.create_notification(
            user_id=str(user_id),
            title="Test",
            message="Test message",
            notification_type="system"
        )
        
        assert notification.title == "Test"
        assert notification.message == "Test message"
        assert notification.user_id == user_id
        mock_db.notifications.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_bin_status_notification(self, service, mock_db):
        """Test creating a bin status notification."""
        user_id = ObjectId()
        mock_db.notifications.insert_one.return_value.inserted_id = ObjectId()
        
        notification = await service.create_bin_status_notification(
            user_id=str(user_id),
            bin_id="bin_001",
            bin_status="full",
            message="Bin is full"
        )
        
        assert notification.notification_type == "bin_status"
        assert notification.bin_id == "bin_001"
        assert notification.bin_status == "full"
        assert notification.priority == 3  # High priority for full bin
    
    @pytest.mark.asyncio
    async def test_create_achievement_notification(self, service, mock_db):
        """Test creating an achievement notification."""
        user_id = ObjectId()
        mock_db.notifications.insert_one.return_value.inserted_id = ObjectId()
        
        notification = await service.create_achievement_notification(
            user_id=str(user_id),
            achievement_type="First Bottle",
            achievement_value=1,
            message="Congratulations!"
        )
        
        assert notification.notification_type == "achievement"
        assert notification.achievement_type == "First Bottle"
        assert notification.achievement_value == 1
        assert notification.title == "Pencapaian Baru: First Bottle"
    
    @pytest.mark.asyncio
    async def test_create_reward_notification(self, service, mock_db):
        """Test creating a reward notification."""
        user_id = ObjectId()
        mock_db.notifications.insert_one.return_value.inserted_id = ObjectId()
        
        notification = await service.create_reward_notification(
            user_id=str(user_id),
            points=10,
            bottle_count=2
        )
        
        assert notification.notification_type == "reward"
        assert notification.title == "Reward Diterima!"
        assert "10 poin" in notification.message
        assert "2 botol" in notification.message
    
    @pytest.mark.asyncio
    async def test_get_user_notifications(self, service, mock_db):
        """Test getting user notifications."""
        user_id = ObjectId()
        mock_notifications = [
            {
                "_id": ObjectId(),
                "user_id": user_id,
                "title": "Test 1",
                "message": "Message 1",
                "notification_type": "system",
                "is_read": False,
                "created_at": datetime.utcnow(),
                "priority": 2
            },
            {
                "_id": ObjectId(),
                "user_id": user_id,
                "title": "Test 2",
                "message": "Message 2",
                "notification_type": "system",
                "is_read": True,
                "created_at": datetime.utcnow(),
                "priority": 1
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.__aiter__.return_value = mock_notifications
        mock_db.notifications.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        notifications = await service.get_user_notifications(user_id=str(user_id))
        
        assert len(notifications) == 2
        assert notifications[0].title == "Test 1"
        assert notifications[1].title == "Test 2"
    
    @pytest.mark.asyncio
    async def test_get_user_notifications_unread_only(self, service, mock_db):
        """Test getting only unread notifications."""
        user_id = ObjectId()
        mock_notifications = [
            {
                "_id": ObjectId(),
                "user_id": user_id,
                "title": "Unread",
                "message": "Unread message",
                "notification_type": "system",
                "is_read": False,
                "created_at": datetime.utcnow(),
                "priority": 2
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.__aiter__.return_value = mock_notifications
        mock_db.notifications.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        notifications = await service.get_user_notifications(
            user_id=str(user_id),
            unread_only=True
        )
        
        assert len(notifications) == 1
        assert notifications[0].title == "Unread"
        # Verify the filter was applied
        mock_db.notifications.find.assert_called_with({
            "user_id": user_id,
            "is_read": False
        })
    
    @pytest.mark.asyncio
    async def test_mark_as_read(self, service, mock_db):
        """Test marking a notification as read."""
        notification_id = ObjectId()
        user_id = ObjectId()
        mock_db.notifications.update_one.return_value.modified_count = 1
        
        result = await service.mark_as_read(str(notification_id), str(user_id))
        
        assert result is True
        mock_db.notifications.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, service, mock_db):
        """Test marking all notifications as read."""
        user_id = ObjectId()
        mock_db.notifications.update_many.return_value.modified_count = 3
        
        result = await service.mark_all_as_read(str(user_id))
        
        assert result == 3
        mock_db.notifications.update_many.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_notification(self, service, mock_db):
        """Test deleting a notification."""
        notification_id = ObjectId()
        user_id = ObjectId()
        mock_db.notifications.delete_one.return_value.deleted_count = 1
        
        result = await service.delete_notification(str(notification_id), str(user_id))
        
        assert result is True
        mock_db.notifications.delete_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_unread_count(self, service, mock_db):
        """Test getting unread count."""
        user_id = ObjectId()
        mock_db.notifications.count_documents.return_value = 5
        
        result = await service.get_unread_count(str(user_id))
        
        assert result == 5
        mock_db.notifications.count_documents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_settings_new_user(self, service, mock_db):
        """Test getting or creating settings for a new user."""
        user_id = ObjectId()
        mock_db.notification_settings.find_one.return_value = None
        mock_db.notification_settings.insert_one.return_value.inserted_id = ObjectId()
        
        settings = await service.get_or_create_settings(str(user_id))
        
        assert settings.user_id == user_id
        assert settings.email_notifications is True  # Default value
        mock_db.notification_settings.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_settings_existing_user(self, service, mock_db):
        """Test getting settings for an existing user."""
        user_id = ObjectId()
        existing_settings = {
            "_id": ObjectId(),
            "user_id": user_id,
            "email_notifications": False,
            "push_notifications": True,
            "bin_status_notifications": True,
            "achievement_notifications": False,
            "system_notifications": True,
            "reward_notifications": True,
            "quiet_hours_start": 23,
            "quiet_hours_end": 6
        }
        mock_db.notification_settings.find_one.return_value = existing_settings
        
        settings = await service.get_or_create_settings(str(user_id))
        
        assert settings.user_id == user_id
        assert settings.email_notifications is False
        assert settings.push_notifications is True
        assert settings.quiet_hours_start == 23
    
    @pytest.mark.asyncio
    async def test_update_settings(self, service, mock_db):
        """Test updating notification settings."""
        user_id = ObjectId()
        mock_db.notifications.update_one.return_value.modified_count = 1
        
        # Mock get_or_create_settings to return updated settings
        with patch.object(service, 'get_or_create_settings') as mock_get:
            mock_get.return_value = NotificationSettings(
                user_id=user_id,
                email_notifications=False,
                push_notifications=True
            )
            
            result = await service.update_settings(
                str(user_id),
                email_notifications=False,
                push_notifications=True
            )
            
            assert result.email_notifications is False
            assert result.push_notifications is True
            mock_db.notification_settings.update_one.assert_called_once()


class TestNotificationSchemas:
    """Test notification schemas."""
    
    def test_notification_create_schema(self):
        """Test notification create schema."""
        data = {
            "user_id": "507f1f77bcf86cd799439011",
            "title": "Test Title",
            "message": "Test message",
            "notification_type": "system",
            "priority": 2
        }
        
        notification = NotificationCreate(**data)
        assert notification.user_id == "507f1f77bcf86cd799439011"
        assert notification.title == "Test Title"
        assert notification.message == "Test message"
        assert notification.notification_type == "system"
        assert notification.priority == 2
    
    def test_notification_settings_update_schema(self):
        """Test notification settings update schema."""
        data = {
            "email_notifications": False,
            "push_notifications": True,
            "quiet_hours_start": 23,
            "quiet_hours_end": 6
        }
        
        settings = NotificationSettingsUpdate(**data)
        assert settings.email_notifications is False
        assert settings.push_notifications is True
        assert settings.quiet_hours_start == 23
        assert settings.quiet_hours_end == 6
    
    def test_notification_type_validation(self):
        """Test notification type validation."""
        with pytest.raises(ValueError):
            NotificationCreate(
                user_id="507f1f77bcf86cd799439011",
                title="Test",
                message="Test",
                notification_type="invalid_type"
            )
    
    def test_priority_validation(self):
        """Test priority validation."""
        with pytest.raises(ValueError):
            NotificationCreate(
                user_id="507f1f77bcf86cd799439011",
                title="Test",
                message="Test",
                notification_type="system",
                priority=5  # Invalid priority
            )
