from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import Field, BaseModel

from .common import MongoBaseModel, PyObjectId


class PersonalStatistics(MongoBaseModel):
    """Personal statistics model for user dashboard."""
    
    user_id: PyObjectId
    total_bottles: int = Field(default=0, ge=0)
    total_points: int = Field(default=0, ge=0)
    total_scans: int = Field(default=0, ge=0)
    
    # Environmental impact (estimated)
    plastic_waste_diverted_kg: float = Field(default=0.0, ge=0.0)  # kg
    co2_emissions_saved_kg: float = Field(default=0.0, ge=0.0)     # kg CO2
    
    # Achievement tracking
    bottles_this_month: int = Field(default=0, ge=0)
    points_this_month: int = Field(default=0, ge=0)
    current_streak_days: int = Field(default=0, ge=0)
    longest_streak_days: int = Field(default=0, ge=0)
    
    # Last activity
    last_scan_date: Optional[datetime] = None
    last_reward_date: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StatisticsSummary(BaseModel):
    """Summary statistics for API response."""
    
    total_bottles: int
    total_points: int
    total_scans: int
    plastic_waste_diverted_kg: float
    co2_emissions_saved_kg: float
    bottles_this_month: int
    points_this_month: int
    current_streak_days: int
    longest_streak_days: int
    last_scan_date: Optional[datetime] = None
    last_reward_date: Optional[datetime] = None
