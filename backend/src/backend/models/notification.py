from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal
from pydantic import Field

from .common import MongoBaseModel, PyObjectId


class Notification(MongoBaseModel):
    """Notification model for various system notifications."""
    
    user_id: PyObjectId
    title: str
    message: str
    notification_type: Literal["bin_status", "achievement", "system", "reward"] = "system"
    
    # For bin status notifications
    bin_id: Optional[str] = None
    bin_status: Optional[Literal["full", "maintenance", "available"]] = None
    
    # For achievement notifications
    achievement_type: Optional[str] = None
    achievement_value: Optional[int] = None
    
    # Metadata
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    
    # Priority level (1=low, 2=medium, 3=high)
    priority: int = Field(default=2, ge=1, le=3)
    
    # Optional action data
    action_url: Optional[str] = None
    action_text: Optional[str] = None


class NotificationSettings(MongoBaseModel):
    """User notification preferences."""
    
    user_id: PyObjectId
    email_notifications: bool = True
    push_notifications: bool = True
    bin_status_notifications: bool = True
    achievement_notifications: bool = True
    system_notifications: bool = True
    reward_notifications: bool = True
    
    # Quiet hours (24-hour format)
    quiet_hours_start: int = Field(default=22, ge=0, le=23)  # 10 PM
    quiet_hours_end: int = Field(default=7, ge=0, le=23)    # 7 AM
