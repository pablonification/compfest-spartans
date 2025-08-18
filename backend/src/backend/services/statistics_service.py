from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId

from ..models.statistics import PersonalStatistics, StatisticsSummary
from ..db.mongo import ensure_connection


class StatisticsService:
    """Service for calculating and managing user statistics."""
    
    def __init__(self):
        pass
    
    async def _get_collections(self):
        db = await ensure_connection()
        return db["scans"], db["users"], db["personal_statistics"]
    
    async def calculate_user_statistics(self, user_id: str | ObjectId) -> StatisticsSummary:
        """Calculate comprehensive statistics for a user."""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            scans_collection, users_collection, _ = await self._get_collections()

            # Resolve user's email from users collection since scans store user_email
            if isinstance(user_id, str):
                user_obj_id = ObjectId(user_id)
            else:
                user_obj_id = user_id
            user_doc = await users_collection.find_one({"_id": user_obj_id})
            if not user_doc:
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
            user_email = user_doc.get("email")
            
            # Get current month start for monthly calculations
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            
            # Aggregate scans data
            pipeline = [
                {"$match": {"user_email": user_email, "valid": True}},
                {"$group": {
                    "_id": None,
                    "total_scans": {"$sum": 1},
                    "total_bottles": {"$sum": 1},
                    "total_points": {"$sum": "$points"},
                    "last_scan_date": {"$max": "$timestamp"},
                    "monthly_bottles": {
                        "$sum": {
                            "$cond": [
                                {"$gte": ["$timestamp", month_start]},
                                1,
                                0
                            ]
                        }
                    },
                    "monthly_points": {
                        "$sum": {
                            "$cond": [
                                {"$gte": ["$timestamp", month_start]},
                                "$points",
                                0
                            ]
                        }
                    }
                }}
            ]
            
            try:
                cursor = scans_collection.aggregate(pipeline)
                result = await cursor.to_list(length=1)
            except Exception as e:
                print(f"Error aggregating scans for user {user_id}: {str(e)}")
                # Return default values on aggregation failure
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
            current_streak, longest_streak = await self._calculate_streak(user_obj_id, user_email)
            
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
            
        except Exception as e:
            print(f"Error calculating statistics for user {user_id}: {str(e)}")
            # Return default values on any error
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
    
    async def _calculate_streak(self, user_id: ObjectId, user_email: str) -> tuple[int, int]:
        """Calculate current and longest streak of consecutive days with scans."""
        try:
            scans_collection, _, _ = await self._get_collections()
            
            # Get all scan dates for user - convert cursor to list to avoid iteration issues
            scan_dates_cursor = scans_collection.find(
                {"user_email": user_email, "valid": True},
                {"timestamp": 1}
            ).sort("timestamp", -1)
            
            # Convert cursor to list to avoid Motor cursor iteration issues
            scan_dates = await scan_dates_cursor.to_list(length=None)
            
            if not scan_dates:
                return 0, 0
            
            dates = []
            for scan in scan_dates:
                # Convert to date only (remove time)
                scan_date = scan["timestamp"].date()
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
            
        except Exception as e:
            # Log the error and return default values
            print(f"Error calculating streak for user {user_id}: {str(e)}")
            return 0, 0
    
    async def update_statistics_after_scan(
        self, 
        user_id: str | ObjectId, 
        bottle_count: int, 
        points_earned: int
    ) -> None:
        """Update user statistics after a new scan."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        scans_collection, users_collection, statistics_collection = await self._get_collections()
        
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
        
        await statistics_collection.update_one(
            {"user_id": user_id},
            update_data,
            upsert=True
        )
    
    async def get_user_rankings(self, limit: int = 10) -> list[dict]:
        """Get top users by total bottles recycled."""
        try:
            scans_collection, users_collection, _ = await self._get_collections()
            
            pipeline = [
                {"$match": {"valid": True}},
                {"$group": {
                    "_id": "$user_email",
                    "total_bottles": {"$sum": 1},
                    "total_points": {"$sum": "$points"}
                }},
                {"$sort": {"total_bottles": -1}},
                {"$limit": limit},
                {"$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "email",
                    "as": "user_info"
                }},
                {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
                {"$project": {
                    "user_id": {"$toString": "$user_info._id"},
                    "name": {"$ifNull": ["$user_info.name", "$_id"]},
                    "total_bottles": 1,
                    "total_points": 1
                }}
            ]
            
            try:
                cursor = scans_collection.aggregate(pipeline)
                rankings = await cursor.to_list(length=limit)
                return rankings
            except Exception as e:
                print(f"Error getting user rankings: {str(e)}")
                return []
                
        except Exception as e:
            print(f"Error in get_user_rankings: {str(e)}")
            return []
