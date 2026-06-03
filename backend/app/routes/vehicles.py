"""Vehicles API endpoints - backed by SQLite database."""

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from ..services.db_service import get_session
from ..models.vehicle_model import VehicleModel

router = APIRouter()


@router.get("")
@router.get("/")
async def list_vehicles(
    vehicle_class: Optional[str] = None,
    active_only: bool = False,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session),
):
    """List tracked vehicles."""
    query = select(VehicleModel).order_by(VehicleModel.last_seen.desc())

    if vehicle_class:
        query = query.where(VehicleModel.vehicle_class == vehicle_class)
    if active_only:
        query = query.where(VehicleModel.is_active == True)

    query = query.limit(limit)
    result = await session.execute(query)
    vehicles = result.scalars().all()

    # Total count
    count_query = select(func.count()).select_from(VehicleModel)
    if vehicle_class:
        count_query = count_query.where(VehicleModel.vehicle_class == vehicle_class)
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    return {"total": total, "vehicles": [v.to_dict() for v in vehicles]}


@router.get("/{track_id}")
async def get_vehicle(track_id: int, session: AsyncSession = Depends(get_session)):
    """Get vehicle by track ID."""
    result = await session.execute(
        select(VehicleModel).where(VehicleModel.track_id == track_id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle.to_dict()


@router.get("/{track_id}/history")
async def vehicle_history(track_id: int, session: AsyncSession = Depends(get_session)):
    """Get vehicle tracking history."""
    result = await session.execute(
        select(VehicleModel).where(VehicleModel.track_id == track_id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        return {"track_id": track_id, "history": [], "message": "Vehicle not found"}

    return {
        "track_id": track_id,
        "vehicle_class": vehicle.vehicle_class,
        "max_speed": vehicle.max_speed,
        "avg_speed": vehicle.avg_speed,
        "violation_count": vehicle.violation_count,
        "first_seen": vehicle.first_seen.isoformat() if vehicle.first_seen else None,
        "last_seen": vehicle.last_seen.isoformat() if vehicle.last_seen else None,
    }
