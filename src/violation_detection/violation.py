"""
Violation Data Models
Defines violation types, severity levels, and data structures.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple
import time
import uuid


class ViolationType(Enum):
    """Types of traffic violations."""
    SPEED = "speed_violation"
    RED_LIGHT = "red_light_violation"
    LANE = "lane_violation"
    ILLEGAL_PARKING = "illegal_parking"
    WRONG_WAY = "wrong_way"
    PHONE_USAGE = "phone_usage"
    NO_SEATBELT = "no_seatbelt"


class Severity(Enum):
    """Violation severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Violation:
    """
    Represents a detected traffic violation.
    """
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    violation_type: ViolationType = ViolationType.SPEED
    severity: Severity = Severity.LOW
    
    # Vehicle info
    track_id: int = 0
    vehicle_class: str = "unknown"
    
    # Location & time
    timestamp: float = field(default_factory=time.time)
    location: Tuple[int, int] = (0, 0)  # pixel coordinates
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
    
    # Violation details
    speed: float = 0.0  # For speed violations
    speed_limit: float = 60.0
    confidence: float = 0.0
    
    # Evidence
    frame_snapshot: Optional[str] = None  # Path to saved frame
    description: str = ""
    
    # Status
    is_confirmed: bool = False
    is_reported: bool = False
    
    @property
    def speed_excess(self) -> float:
        """How much over the speed limit."""
        return max(0, self.speed - self.speed_limit)
    
    @property
    def time_str(self) -> str:
        """Formatted timestamp string."""
        import datetime
        return datetime.datetime.fromtimestamp(self.timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    
    def to_dict(self) -> dict:
        """Convert violation to dictionary for storage/API."""
        return {
            "violation_id": self.violation_id,
            "type": self.violation_type.value,
            "severity": self.severity.value,
            "track_id": self.track_id,
            "vehicle_class": self.vehicle_class,
            "timestamp": self.timestamp,
            "time_str": self.time_str,
            "location": self.location,
            "bbox": self.bbox,
            "speed": self.speed,
            "speed_limit": self.speed_limit,
            "speed_excess": self.speed_excess,
            "confidence": self.confidence,
            "description": self.description,
            "is_confirmed": self.is_confirmed,
            "is_reported": self.is_reported,
            "frame_snapshot": self.frame_snapshot,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Violation":
        """Create violation from dictionary."""
        return cls(
            violation_id=data.get("violation_id", str(uuid.uuid4())),
            violation_type=ViolationType(data.get("type", "speed_violation")),
            severity=Severity(data.get("severity", "low")),
            track_id=data.get("track_id", 0),
            vehicle_class=data.get("vehicle_class", "unknown"),
            timestamp=data.get("timestamp", time.time()),
            location=tuple(data.get("location", (0, 0))),
            bbox=tuple(data.get("bbox", (0, 0, 0, 0))),
            speed=data.get("speed", 0.0),
            speed_limit=data.get("speed_limit", 60.0),
            confidence=data.get("confidence", 0.0),
            description=data.get("description", ""),
            is_confirmed=data.get("is_confirmed", False),
            is_reported=data.get("is_reported", False),
            frame_snapshot=data.get("frame_snapshot"),
        )
