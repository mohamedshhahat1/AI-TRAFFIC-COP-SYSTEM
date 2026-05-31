"""Vehicles API endpoints."""

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

_vehicles = []


@router.get("/")
async def list_vehicles(
    vehicle_class: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """List tracked vehicles."""
    filtered = _vehicles
    if vehicle_class:
        filtered = [v for v in filtered if v.get("class") == vehicle_class]
    return {"total": len(filtered), "vehicles": filtered[-limit:]}


@router.get("/{track_id}")
async def get_vehicle(track_id: int):
    """Get vehicle by track ID."""
    for v in _vehicles:
        if v.get("track_id") == track_id:
            return v
    return {"error": "Not found"}


@router.get("/{track_id}/history")
async def vehicle_history(track_id: int):
    """Get vehicle tracking history."""
    return {"track_id": track_id, "history": []}
