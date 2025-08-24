from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from ..models.common import PyObjectId


class NotificationBase(BaseModel):
    """Base notification schema."""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    notification_type: str = Field(..., pattern="^(bin_status|achievement|system|reward)$")
    priority: int = Field(default=2, ge=1, le=3)


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""
    user_id: str
    bin_id: Optional[str] = None
    bin_status: Optional[str] = None
    achievement_type: Optional[str] = None
    achievement_value: Optional[int] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    bin_id: Optional[str] = None
    bin_status: Optional[str] = None
    achievement_type: Optional[str] = None
    achievement_value: Optional[int] = None
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    priority: int
    action_url: Optional[str] = None
    action_text: Optional[str] = None


class NotificationUpdate(BaseModel):
    """Schema for updating notification (mark as read)."""
    is_read: bool = True


class NotificationListResponse(BaseModel):
    """Schema for list of notifications."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationSettingsUpdate(BaseModel):
    """Schema for updating notification settings."""
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    bin_status_notifications: Optional[bool] = None
    achievement_notifications: Optional[bool] = None
    system_notifications: Optional[bool] = None
    reward_notifications: Optional[bool] = None
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)


class NotificationSettingsResponse(BaseModel):
    """Schema for notification settings response."""
    id: str
    user_id: str
    email_notifications: bool
    push_notifications: bool
    bin_status_notifications: bool
    achievement_notifications: bool
    system_notifications: bool
    reward_notifications: bool
    quiet_hours_start: int
    quiet_hours_end: int


class BinStatusNotification(BaseModel):
    """Schema for bin status notification."""
    bin_id: str
    bin_status: str = Field(..., pattern="^(full|maintenance|available)$")
    message: str = Field(..., min_length=1, max_length=500)


class AchievementNotification(BaseModel):
    """Schema for achievement notification."""
    achievement_type: str = Field(..., min_length=1, max_length=100)
    achievement_value: int = Field(..., ge=1)
    message: str = Field(..., min_length=1, max_length=500)
