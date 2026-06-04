"""
License Plates API Routes
ANPR endpoints for plate lookup, search, and evidence.
"""

import json
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
from typing import Optional

router = APIRouter()

# Initialize registry service
try:
    from backend.app.services.vehicle_registry import VehicleRegistryService
    registry = VehicleRegistryService()
except Exception:
    registry = None


def json_response(data):
    """Return JSON response with proper UTF-8 encoding for Arabic text."""
    return Response(
        content=json.dumps(data, ensure_ascii=False),
        media_type="application/json; charset=utf-8",
    )


@router.get("")
@router.get("/")
async def list_plates():
    """List all registered vehicles."""
    if registry:
        return json_response({"total": len(registry.get_all()), "vehicles": registry.get_all()})
    return json_response({"total": 0, "vehicles": {}})


@router.get("/lookup/{plate_number}")
async def lookup_plate(plate_number: str):
    """Look up a specific plate number."""
    if not registry:
        raise HTTPException(status_code=503, detail="Registry not available")

    info = registry.lookup(plate_number)
    if info:
        return json_response(info)
    raise HTTPException(status_code=404, detail="Plate not found")


@router.get("/search")
async def search_plates(q: str = Query(..., description="Search by plate, owner, or vehicle")):
    """Search vehicle registry."""
    if not registry:
        return json_response({"results": []})
    return json_response({"results": registry.search(q)})


@router.post("/register")
async def register_vehicle(plate: str, owner: str, vehicle: str, color: str = "Unknown"):
    """Register a new vehicle."""
    if not registry:
        raise HTTPException(status_code=503, detail="Registry not available")
    registry.add_vehicle(plate, owner, vehicle, color)
    return {"status": "registered", "plate": plate}


@router.get("/stats")
async def plate_stats():
    """Get ANPR statistics."""
    return {
        "registry_size": len(registry.get_all()) if registry else 0,
        "anpr_available": registry is not None,
    }
