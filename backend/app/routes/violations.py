"""Violations API endpoints."""

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

# In-memory store (replace with DB in production)
_violations = []


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
    return {"error": "Not found"}


@router.post("/")
async def create_violation(data: dict):
    """Record a new violation."""
    _violations.append(data)
    return {"status": "created", "violation": data}


@router.get("/summary/today")
async def today_summary():
    """Today's violation summary."""
    import time
    today_start = time.time() - 86400
    today = [v for v in _violations if v.get("timestamp", 0) > today_start]
    
    by_type = {}
    for v in today:
        t = v.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
    
    return {"total": len(today), "by_type": by_type}
