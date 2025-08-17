from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId

from ..models.statistics import PersonalStatistics, StatisticsSummary
from ..db.mongo import get_database


class StatisticsService:
    """Service for calculating and managing user statistics."""
    
    def __init__(self):
        self.db = get_database()
        self.scans_collection = self.db.scans
        self.users_collection = self.db.users
        self.statistics_collection = self.db.personal_statistics
    
    async def calculate_user_statistics(self, user_id: str | ObjectId) -> StatisticsSummary:
        """Calculate comprehensive statistics for a user."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        # Get current month boundaries
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        # Aggregate scans data
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_scans": {"$sum": 1},
                "total_bottles": {"$sum": "$bottle_count"},
                "total_points": {"$sum": "$points_earned"},
                "last_scan_date": {"$max": "$created_at"},
                "monthly_bottles": {
                    "$sum": {
                        "$cond": [
                            {"$gte": ["$created_at", month_start]},
                            "$bottle_count",
                            0
                        ]
                    }
                },
                "monthly_points": {
                    "$sum": {
                        "$cond": [
                            {"$gte": ["$created_at", month_start]},
                            "$points_earned",
                            0
                        ]
                    }
                }
            }}
        ]
        
        result = list(self.scans_collection.aggregate(pipeline))
        
        if not result:
            # No scans found, return default values
            return StatisticsSummary(
                total_bottles=0,
                total_points=0,
                total_scans=0,
                plastic_waste_diverted_kg=0.0,
                co2_emissions_saved_kg=0.0,
                bottles_this_month=0,
                points_this_month=0,
                current_streak_days=0,
                longest_streak_days=0
            )
        
        stats = result[0]
        
        # Calculate environmental impact (estimates)
        # Average plastic bottle: ~25g, CO2 saved per bottle: ~0.1kg
        plastic_waste_diverted_kg = (stats.get("total_bottles", 0) * 25) / 1000
        co2_emissions_saved_kg = stats.get("total_bottles", 0) * 0.1
        
        # Calculate streak (consecutive days with scans)
        current_streak, longest_streak = await self._calculate_streak(user_id)
        
        return StatisticsSummary(
            total_bottles=stats.get("total_bottles", 0),
            total_points=stats.get("total_points", 0),
            total_scans=stats.get("total_scans", 0),
            plastic_waste_diverted_kg=plastic_waste_diverted_kg,
            co2_emissions_saved_kg=co2_emissions_saved_kg,
            bottles_this_month=stats.get("monthly_bottles", 0),
            points_this_month=stats.get("monthly_points", 0),
            current_streak_days=current_streak,
            longest_streak_days=longest_streak,
            last_scan_date=stats.get("last_scan_date"),
            last_reward_date=stats.get("last_scan_date")  # Assuming reward given on scan
        )
    
    async def _calculate_streak(self, user_id: ObjectId) -> tuple[int, int]:
        """Calculate current and longest streak of consecutive days with scans."""
        # Get all scan dates for user
        scan_dates = self.scans_collection.find(
            {"user_id": user_id},
            {"created_at": 1}
        ).sort("created_at", -1)
        
        dates = []
        async for scan in scan_dates:
            # Convert to date only (remove time)
            scan_date = scan["created_at"].date()
            if scan_date not in dates:
                dates.append(scan_date)
        
        if not dates:
            return 0, 0
        
        # Calculate current streak
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        today = datetime.utcnow().date()
        current_date = today
        
        for i, scan_date in enumerate(dates):
            if i == 0:
                # First scan
                if scan_date == today:
                    temp_streak = 1
                    current_streak = 1
                elif scan_date == today - timedelta(days=1):
                    temp_streak = 1
                    current_streak = 1
                else:
                    temp_streak = 0
                    current_streak = 0
            else:
                # Check if consecutive
                if scan_date == current_date - timedelta(days=1):
                    temp_streak += 1
                    if temp_streak > longest_streak:
                        longest_streak = temp_streak
                    if scan_date == today - timedelta(days=1):
                        current_streak = temp_streak
                else:
                    temp_streak = 1
                    if temp_streak > longest_streak:
                        longest_streak = temp_streak
            
            current_date = scan_date
        
        return current_streak, longest_streak
    
    async def update_statistics_after_scan(
        self, 
        user_id: str | ObjectId, 
        bottle_count: int, 
        points_earned: int
    ) -> None:
        """Update user statistics after a new scan."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        # Update or create statistics document
        update_data = {
            "$inc": {
                "total_bottles": bottle_count,
                "total_points": points_earned,
                "total_scans": 1
            },
            "$set": {
                "last_scan_date": datetime.utcnow(),
                "last_reward_date": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
        
        # Update monthly stats
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        if now >= month_start:
            update_data["$inc"]["bottles_this_month"] = bottle_count
            update_data["$inc"]["points_this_month"] = points_earned
        
        await self.statistics_collection.update_one(
            {"user_id": user_id},
            update_data,
            upsert=True
        )
    
    async def get_user_rankings(self, limit: int = 10) -> list[dict]:
        """Get top users by total bottles recycled."""
        pipeline = [
            {"$group": {
                "_id": "$user_id",
                "total_bottles": {"$sum": "$bottle_count"},
                "total_points": {"$sum": "$points_earned"}
            }},
            {"$sort": {"total_bottles": -1}},
            {"$limit": limit},
            {"$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_info"
            }},
            {"$unwind": "$user_info"},
            {"$project": {
                "user_id": "$_id",
                "name": "$user_info.name",
                "total_bottles": 1,
                "total_points": 1
            }}
        ]
        
        rankings = []
        async for rank in self.scans_collection.aggregate(pipeline):
            rankings.append(rank)
        
        return rankings
