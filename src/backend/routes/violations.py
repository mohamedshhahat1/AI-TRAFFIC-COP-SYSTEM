"""
Violations API Routes
CRUD operations for traffic violations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from datetime import datetime, timedelta

from ..database.db import get_db
from ..database.models import Violation

router = APIRouter()


@router.get("/")
async def list_violations(
    violation_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all violations with optional filtering."""
    query = select(Violation).order_by(desc(Violation.timestamp))
    
    if violation_type:
        query = query.where(Violation.violation_type == violation_type)
    if severity:
        query = query.where(Violation.severity == severity)
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    violations = result.scalars().all()
    
    return {
        "total": len(violations),
        "violations": [v.to_dict() for v in violations]
    }


@router.get("/{violation_id}")
async def get_violation(violation_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific violation by ID."""
    query = select(Violation).where(Violation.violation_id == violation_id)
    result = await db.execute(query)
    violation = result.scalar_one_or_none()
    
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    
    return violation.to_dict()


@router.post("/")
async def create_violation(violation_data: dict, db: AsyncSession = Depends(get_db)):
    """Create a new violation record."""
    violation = Violation(
        violation_id=violation_data.get("violation_id"),
        violation_type=violation_data.get("type"),
        severity=violation_data.get("severity"),
        track_id=violation_data.get("track_id", 0),
        vehicle_class=violation_data.get("vehicle_class", "unknown"),
        location_x=violation_data.get("location", {}).get("x", 0),
        location_y=violation_data.get("location", {}).get("y", 0),
        speed=violation_data.get("speed", 0.0),
        speed_limit=violation_data.get("speed_limit", 60.0),
        confidence=violation_data.get("confidence", 0.0),
        description=violation_data.get("description", ""),
        frame_snapshot=violation_data.get("frame_snapshot"),
        is_confirmed=violation_data.get("is_confirmed", False),
    )
    
    db.add(violation)
    await db.commit()
    await db.refresh(violation)
    
    return {"status": "created", "violation": violation.to_dict()}


@router.delete("/{violation_id}")
async def delete_violation(violation_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a violation record."""
    query = select(Violation).where(Violation.violation_id == violation_id)
    result = await db.execute(query)
    violation = result.scalar_one_or_none()
    
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    
    await db.delete(violation)
    await db.commit()
    
    return {"status": "deleted", "violation_id": violation_id}


@router.get("/summary/today")
async def today_summary(db: AsyncSession = Depends(get_db)):
    """Get today's violation summary."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    query = select(Violation).where(Violation.timestamp >= today)
    result = await db.execute(query)
    violations = result.scalars().all()
    
    summary = {
        "total": len(violations),
        "by_type": {},
        "by_severity": {},
    }
    
    for v in violations:
        summary["by_type"][v.violation_type] = summary["by_type"].get(v.violation_type, 0) + 1
        summary["by_severity"][v.severity] = summary["by_severity"].get(v.severity, 0) + 1
    
    return summary
