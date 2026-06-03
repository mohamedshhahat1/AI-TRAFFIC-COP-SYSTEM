"""Violations API endpoints."""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
import time
import uuid

from ..middleware.auth import api_key_auth

router = APIRouter()

# In-memory store (replace with DB in production)
_violations = []


# Pydantic model for request validation
class ViolationCreate(BaseModel):
    type: str = Field(..., description="Violation type (speed_violation, red_light_violation, etc.)")
    severity: str = Field(default="low", description="Severity level")
    track_id: int = Field(default=0)
    vehicle_class: str = Field(default="car")
    speed: float = Field(default=0.0)
    speed_limit: float = Field(default=60.0)
    description: str = Field(default="")


# IMPORTANT: Static routes MUST come before parameterized routes
@router.get("/summary/today")
async def today_summary():
    """Today's violation summary."""
    from datetime import datetime, timezone
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).timestamp()
    today = [v for v in _violations if v.get("timestamp", 0) > today_start]

    by_type = {}
    for v in today:
        t = v.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    return {"total": len(today), "by_type": by_type}


@router.get("")
@router.get("/")
async def list_violations(
    type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """List violations with optional filtering."""
    filtered = _violations
    if type:
        filtered = [v for v in filtered if v.get("type") == type]
    if severity:
        filtered = [v for v in filtered if v.get("severity") == severity]
    return {"total": len(filtered), "violations": filtered[-limit:]}


@router.get("/{violation_id}")
async def get_violation(violation_id: str):
    """Get violation by ID."""
    for v in _violations:
        if v.get("id") == violation_id:
            return v
    raise HTTPException(status_code=404, detail="Violation not found")


@router.post("/")
async def create_violation(data: ViolationCreate):
    """Record a new violation (validated)."""
    violation = {
        "id": str(uuid.uuid4())[:8],
        "type": data.type,
        "severity": data.severity,
        "track_id": data.track_id,
        "vehicle_class": data.vehicle_class,
        "speed": data.speed,
        "speed_limit": data.speed_limit,
        "description": data.description,
        "timestamp": time.time(),
    }
    _violations.append(violation)
    return {"status": "created", "violation": violation}


@router.delete("/{violation_id}")
async def delete_violation(violation_id: str, _user: str = Depends(api_key_auth)):
    """Delete a violation by ID (requires authentication)."""
    global _violations
    before = len(_violations)
    _violations = [v for v in _violations if v.get("id") != violation_id]
    if len(_violations) == before:
        raise HTTPException(status_code=404, detail="Violation not found")
    return {"status": "deleted", "violation_id": violation_id}
