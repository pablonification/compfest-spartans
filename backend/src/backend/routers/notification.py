from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
    NotificationListResponse,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
    BinStatusNotification,
    AchievementNotification
)
from ..services.notification_service import get_notification_service
from ..routers.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    unread_only: bool = Query(default=False)
):
    """Get user notifications."""
    try:
        notification_service = get_notification_service()
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            unread_only=unread_only
        )
        
        notification_service = get_notification_service()
        unread_count = await notification_service.get_unread_count(current_user.id)
        
        # Convert to response format
        notification_responses = []
        for notif in notifications:
            notif_dict = notif.model_dump()
            notif_dict["id"] = str(notif.id)
            notif_dict["user_id"] = str(notif.user_id)
            notification_responses.append(NotificationResponse(**notif_dict))
        
        return NotificationListResponse(
            notifications=notification_responses,
            total=len(notification_responses),
            unread_count=unread_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {str(e)}")


@router.get("/unread-count")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    """Get count of unread notifications."""
    try:
        notification_service = get_notification_service()
        count = await notification_service.get_unread_count(current_user.id)
        return {"unread_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unread count: {str(e)}")


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    try:
        notification_service = get_notification_service()
        success = await notification_service.mark_as_read(notification_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")


@router.patch("/mark-all-read")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read."""
    try:
        notification_service = get_notification_service()
        count = await notification_service.mark_all_as_read(current_user.id)
        return {"message": f"Marked {count} notifications as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark all notifications as read: {str(e)}")


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification."""
    try:
        notification_service = get_notification_service()
        success = await notification_service.delete_notification(notification_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete notification: {str(e)}")


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(current_user: User = Depends(get_current_user)):
    """Get user notification settings."""
    try:
        notification_service = get_notification_service()
        settings = await notification_service.get_or_create_settings(current_user.id)
        
        settings_dict = settings.model_dump()
        settings_dict["id"] = str(settings.id)
        settings_dict["user_id"] = str(settings.user_id)
        
        return NotificationSettingsResponse(**settings_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification settings: {str(e)}")


@router.patch("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_update: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user notification settings."""
    try:
        notification_service = get_notification_service()
        settings = await notification_service.update_settings(
            current_user.id,
            **settings_update.model_dump(exclude_unset=True)
        )
        
        settings_dict = settings.model_dump()
        settings_dict["id"] = str(settings.id)
        settings_dict["user_id"] = str(settings.user_id)
        
        return NotificationSettingsResponse(**settings_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update notification settings: {str(e)}")


# Admin endpoints for creating notifications
@router.post("/admin/bin-status")
async def create_bin_status_notification(
    notification: BinStatusNotification,
    current_user: User = Depends(get_current_user)
):
    """Create a bin status notification (admin only)."""
    try:
        # For now, allow any authenticated user to create bin status notifications
        # In production, you might want to check if user has admin role
        
        # Create notification for all users (you might want to filter by location)
        # For MVP, we'll create for the current user only
        notification_service = get_notification_service()
        created_notification = await notification_service.create_bin_status_notification(
            user_id=current_user.id,
            bin_id=notification.bin_id,
            bin_status=notification.bin_status,
            message=notification.message
        )
        
        return {"message": "Bin status notification created", "id": str(created_notification.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bin status notification: {str(e)}")


@router.post("/admin/achievement")
async def create_achievement_notification(
    notification: AchievementNotification,
    current_user: User = Depends(get_current_user)
):
    """Create an achievement notification (admin only)."""
    try:
        notification_service = get_notification_service()
        created_notification = await notification_service.create_achievement_notification(
            user_id=current_user.id,
            achievement_type=notification.achievement_type,
            achievement_value=notification.achievement_value,
            message=notification.message
        )
        
        return {"message": "Achievement notification created", "id": str(created_notification.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create achievement notification: {str(e)}")


@router.post("/admin/system")
async def create_system_notification(
    notification: NotificationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a system notification (admin only)."""
    try:
        notification_service = get_notification_service()
        created_notification = await notification_service.create_notification(
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            priority=notification.priority,
            bin_id=notification.bin_id,
            bin_status=notification.bin_status,
            achievement_type=notification.achievement_type,
            achievement_value=notification.achievement_value,
            action_url=notification.action_url,
            action_text=notification.action_text
        )
        
        return {"message": "System notification created", "id": str(created_notification.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create system notification: {str(e)}")
