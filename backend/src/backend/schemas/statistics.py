from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StatisticsSummaryResponse(BaseModel):
    """Response model for personal statistics."""
    
    total_bottles: int = Field(..., description="Total bottles recycled")
    total_points: int = Field(..., description="Total points earned")
    total_scans: int = Field(..., description="Total scan sessions")
    
    # Environmental impact
    plastic_waste_diverted_kg: float = Field(..., description="Plastic waste diverted in kg")
    co2_emissions_saved_kg: float = Field(..., description="CO2 emissions saved in kg")
    
    # Monthly progress
    bottles_this_month: int = Field(..., description="Bottles recycled this month")
    points_this_month: int = Field(..., description="Points earned this month")
    
    # Achievement tracking
    current_streak_days: int = Field(..., description="Current consecutive days streak")
    longest_streak_days: int = Field(..., description="Longest consecutive days streak")
    
    # Last activity
    last_scan_date: Optional[datetime] = Field(None, description="Date of last scan")
    last_reward_date: Optional[datetime] = Field(None, description="Date of last reward")
    
    # Environmental impact summary
    environmental_impact: dict = Field(..., description="Environmental impact summary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_bottles": 45,
                "total_points": 225,
                "total_scans": 23,
                "plastic_waste_diverted_kg": 1.125,
                "co2_emissions_saved_kg": 4.5,
                "bottles_this_month": 12,
                "points_this_month": 60,
                "current_streak_days": 5,
                "longest_streak_days": 12,
                "last_scan_date": "2024-01-15T10:30:00Z",
                "last_reward_date": "2024-01-15T10:30:00Z",
                "environmental_impact": {
                    "bottles_equivalent": "45 botol plastik",
                    "plastic_waste": "1.125 kg sampah plastik",
                    "co2_saved": "4.5 kg CO2",
                    "trees_equivalent": "0.23 pohon (berdasarkan 20 kg CO2 per pohon per tahun)"
                }
            }
        }


class UserRankingResponse(BaseModel):
    """Response model for user rankings."""
    
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    total_bottles: int = Field(..., description="Total bottles recycled")
    total_points: int = Field(..., description="Total points earned")
    rank: int = Field(..., description="User rank position")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "name": "John Doe",
                "total_bottles": 150,
                "total_points": 750,
                "rank": 1
            }
        }


class LeaderboardResponse(BaseModel):
    """Response model for leaderboard."""
    
    rankings: list[UserRankingResponse] = Field(..., description="List of top users")
    total_participants: int = Field(..., description="Total number of participants")
    user_rank: Optional[int] = Field(None, description="Current user's rank (if authenticated)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rankings": [
                    {
                        "user_id": "507f1f77bcf86cd799439011",
                        "name": "John Doe",
                        "total_bottles": 150,
                        "total_points": 750,
                        "rank": 1
                    }
                ],
                "total_participants": 25,
                "user_rank": 3
            }
        }
