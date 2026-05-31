"""
Vehicles API Routes
Vehicle tracking data endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from ..database.db import get_db
from ..database.models import Vehicle

router = APIRouter()


@router.get("/")
async def list_vehicles(
    vehicle_class: Optional[str] = None,
    active_only: bool = True,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """List all tracked vehicles."""
    query = select(Vehicle).order_by(desc(Vehicle.last_seen))
    
    if vehicle_class:
        query = query.where(Vehicle.vehicle_class == vehicle_class)
    if active_only:
        query = query.where(Vehicle.is_active == True)
    
    query = query.limit(limit)
    result = await db.execute(query)
    vehicles = result.scalars().all()
    
    return {
        "total": len(vehicles),
        "vehicles": [v.to_dict() for v in vehicles]
    }


@router.get("/{track_id}")
async def get_vehicle(track_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific vehicle by track ID."""
    query = select(Vehicle).where(Vehicle.track_id == track_id)
    result = await db.execute(query)
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return vehicle.to_dict()


@router.get("/{track_id}/violations")
async def get_vehicle_violations(
    track_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Get all violations for a specific vehicle."""
    from ..database.models import Violation
    
    query = select(Violation).where(
        Violation.track_id == track_id
    ).order_by(desc(Violation.timestamp))
    
    result = await db.execute(query)
    violations = result.scalars().all()
    
    return {
        "track_id": track_id,
        "total_violations": len(violations),
        "violations": [v.to_dict() for v in violations]
    }
