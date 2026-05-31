"""Analytics API endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_analytics():
    """Get overall system analytics."""
    return {
        "total_violations": 0,
        "total_vehicles": 0,
        "avg_speed": 0,
        "congestion_level": "free",
        "system_uptime": "0h",
    }


@router.get("/congestion")
async def congestion_data():
    """Get real-time congestion data."""
    return {
        "current_level": "free",
        "density": 0,
        "prediction": "stable",
    }


@router.get("/heatmap")
async def violation_heatmap():
    """Get violation location heatmap data."""
    return {"hotspots": []}


@router.get("/trends")
async def traffic_trends():
    """Get traffic trend data."""
    return {
        "hourly_violations": {},
        "daily_vehicles": {},
        "peak_hours": [],
    }
