"""Violations API endpoints - backed by SQLite database."""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import select, delete as sql_delete, func
from sqlalchemy.ext.asyncio import AsyncSession
import time
import uuid

from ..middleware.auth import api_key_auth
from ..services.db_service import get_session
from ..models.violation_model import ViolationModel

router = APIRouter()

# In-memory cache for real-time (last 100 violations) - supplements DB
_violations_cache = []


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
async def today_summary(session: AsyncSession = Depends(get_session)):
    """Today's violation summary."""
    from datetime import datetime, timezone
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await session.execute(
        select(ViolationModel).where(ViolationModel.timestamp >= today_start)
    )
    today_violations = result.scalars().all()

    by_type = {}
    for v in today_violations:
        t = v.type or "unknown"
        by_type[t] = by_type.get(t, 0) + 1

    return {"total": len(today_violations), "by_type": by_type}


@router.get("")
@router.get("/")
async def list_violations(
    type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session),
):
    """List violations with optional filtering."""
    query = select(ViolationModel).order_by(ViolationModel.timestamp.desc())

    if type:
        query = query.where(ViolationModel.type == type)
    if severity:
        query = query.where(ViolationModel.severity == severity)

    query = query.limit(limit)
    result = await session.execute(query)
    violations = result.scalars().all()

    # Count total (without limit)
    count_query = select(func.count()).select_from(ViolationModel)
    if type:
        count_query = count_query.where(ViolationModel.type == type)
    if severity:
        count_query = count_query.where(ViolationModel.severity == severity)
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    return {
        "total": total,
        "violations": [v.to_dict() for v in violations]
    }


@router.get("/{violation_id}")
async def get_violation(violation_id: str, session: AsyncSession = Depends(get_session)):
    """Get violation by ID."""
    result = await session.execute(
        select(ViolationModel).where(ViolationModel.violation_id == violation_id)
    )
    violation = result.scalar_one_or_none()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    return violation.to_dict()


@router.post("/")
async def create_violation(data: ViolationCreate, session: AsyncSession = Depends(get_session)):
    """Record a new violation (validated)."""
    violation_id = str(uuid.uuid4())[:8]

    violation = ViolationModel(
        violation_id=violation_id,
        type=data.type,
        severity=data.severity,
        track_id=data.track_id,
        vehicle_class=data.vehicle_class,
        speed=data.speed,
        speed_limit=data.speed_limit,
        description=data.description,
    )
    session.add(violation)
    await session.commit()
    await session.refresh(violation)

    # Update cache
    _violations_cache.append(violation.to_dict())
    if len(_violations_cache) > 100:
        _violations_cache.pop(0)

    return {"status": "created", "violation": violation.to_dict()}


@router.delete("/{violation_id}")
async def delete_violation(
    violation_id: str,
    session: AsyncSession = Depends(get_session),
    _user: str = Depends(api_key_auth),
):
    """Delete a violation by ID (requires authentication)."""
    result = await session.execute(
        select(ViolationModel).where(ViolationModel.violation_id == violation_id)
    )
    violation = result.scalar_one_or_none()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    await session.delete(violation)
    await session.commit()

    return {"status": "deleted", "violation_id": violation_id}
