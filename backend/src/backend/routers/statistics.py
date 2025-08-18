from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..schemas.statistics import (
    StatisticsSummaryResponse,
    UserRankingResponse,
    LeaderboardResponse
)
from ..services.statistics_service import StatisticsService
from ..db.mongo import ensure_connection
from ..routers.auth import verify_token
from bson import ObjectId

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/personal", response_model=StatisticsSummaryResponse)
async def get_personal_statistics(payload: dict = Depends(verify_token)):
    """Get personal statistics for the authenticated user."""
    try:
        user_id = payload["sub"]
        service = StatisticsService()
        
        # Calculate statistics
        stats = await service.calculate_user_statistics(user_id)
        
        # Add environmental impact summary
        environmental_impact = {
            "bottles_equivalent": f"{stats.total_bottles} botol plastik",
            "plastic_waste": f"{stats.plastic_waste_diverted_kg:.3f} kg sampah plastik",
            "co2_saved": f"{stats.co2_emissions_saved_kg:.1f} kg CO2",
            "trees_equivalent": f"{stats.co2_emissions_saved_kg / 20:.2f} pohon (berdasarkan 20 kg CO2 per pohon per tahun)"
        }
        
        # Convert to response model
        response_data = stats.dict()
        response_data["environmental_impact"] = environmental_impact
        
        return StatisticsSummaryResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = 10,
    payload: dict = Depends(verify_token)
):
    """Get top users leaderboard."""
    try:
        if limit > 50:
            limit = 50  # Cap at 50 users
        
        service = StatisticsService()
        rankings = await service.get_user_rankings(limit)
        
        # Add rank numbers
        for i, rank in enumerate(rankings):
            rank["rank"] = i + 1
        
        # Get total participants count
        # Count unique participants with at least one valid scan across all data
        try:
            db = await ensure_connection()
            distinct_emails = await db["scans"].distinct("user_email", {"valid": True})
            total_participants = len(distinct_emails)
        except Exception:
            total_participants = len(rankings)
        
        # Get current user's rank
        user_id = payload["sub"]
        user_rank = None
        for rank in rankings:
            if str(rank.get("user_id")) == str(user_id):
                user_rank = rank.get("rank")
                break
        
        return LeaderboardResponse(
            rankings=[UserRankingResponse(**rank) for rank in rankings],
            total_participants=total_participants,
            user_rank=user_rank
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")


@router.get("/public/leaderboard", response_model=LeaderboardResponse)
async def get_public_leaderboard(limit: int = 10):
    """Get public leaderboard (no authentication required)."""
    try:
        if limit > 50:
            limit = 50
        
        service = StatisticsService()
        rankings = await service.get_user_rankings(limit)
        
        # Add rank numbers
        for i, rank in enumerate(rankings):
            rank["rank"] = i + 1
        
        total_participants = len(rankings)
        
        return LeaderboardResponse(
            rankings=[UserRankingResponse(**rank) for rank in rankings],
            total_participants=total_participants,
            user_rank=None  # No user context for public endpoint
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")
