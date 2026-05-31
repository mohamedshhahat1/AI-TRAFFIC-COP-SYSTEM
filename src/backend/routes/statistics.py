"""
Statistics API Routes
Traffic analytics and reporting endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta

from ..database.db import get_db
from ..database.models import Violation, Vehicle

router = APIRouter()


@router.get("/")
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """Get overall traffic statistics."""
    # Total violations
    total_query = select(func.count(Violation.id))
    total_result = await db.execute(total_query)
    total_violations = total_result.scalar() or 0
    
    # Total vehicles
    vehicle_query = select(func.count(Vehicle.id))
    vehicle_result = await db.execute(vehicle_query)
    total_vehicles = vehicle_result.scalar() or 0
    
    # Today's violations
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_query = select(func.count(Violation.id)).where(Violation.timestamp >= today)
    today_result = await db.execute(today_query)
    today_violations = today_result.scalar() or 0
    
    # Average speed
    avg_speed_query = select(func.avg(Vehicle.avg_speed)).where(Vehicle.avg_speed > 0)
    avg_result = await db.execute(avg_speed_query)
    avg_speed = avg_result.scalar() or 0
    
    return {
        "total_violations": total_violations,
        "total_vehicles_tracked": total_vehicles,
        "today_violations": today_violations,
        "average_speed": round(float(avg_speed), 1),
        "system_status": "active",
    }


@router.get("/violations-by-hour")
async def violations_by_hour(db: AsyncSession = Depends(get_db)):
    """Get violation count by hour for the last 24 hours."""
    now = datetime.utcnow()
    hours_ago_24 = now - timedelta(hours=24)
    
    query = select(Violation).where(Violation.timestamp >= hours_ago_24)
    result = await db.execute(query)
    violations = result.scalars().all()
    
    # Group by hour
    hourly = {}
    for v in violations:
        hour = v.timestamp.hour if v.timestamp else 0
        hourly[hour] = hourly.get(hour, 0) + 1
    
    return {"period": "24h", "data": hourly}


@router.get("/violations-by-type")
async def violations_by_type(db: AsyncSession = Depends(get_db)):
    """Get violation distribution by type."""
    query = select(
        Violation.violation_type, func.count(Violation.id)
    ).group_by(Violation.violation_type)
    
    result = await db.execute(query)
    data = {row[0]: row[1] for row in result.all()}
    
    return {"data": data}


@router.get("/top-offenders")
async def top_offenders(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get top repeat offenders."""
    query = select(Vehicle).where(
        Vehicle.violation_count > 0
    ).order_by(desc(Vehicle.violation_count)).limit(limit)
    
    result = await db.execute(query)
    vehicles = result.scalars().all()
    
    return {
        "top_offenders": [v.to_dict() for v in vehicles]
    }
