"""
Violation Engine - Orchestrates all violation detectors.
Central controller that runs all detection checks per frame.
"""

import cv2
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("violation_engine")
except ImportError:
    from loguru import logger
import time
import uuid
from pathlib import Path

from .speed_violation import SpeedViolationDetector
from .red_light import RedLightDetector
from .lane_violation import LaneViolationDetector
from .parking_violation import ParkingViolationDetector


class ViolationType(Enum):
    SPEED = "speed_violation"
    RED_LIGHT = "red_light_violation"
    LANE = "lane_violation"
    PARKING = "parking_violation"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ViolationRecord:
    """Unified violation record."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: ViolationType = ViolationType.SPEED
    severity: str = "low"
    track_id: int = 0
    vehicle_class: str = "unknown"
    speed: float = 0.0
    speed_limit: float = 60.0
    timestamp: float = field(default_factory=time.time)
    location: tuple = (0, 0)
    bbox: tuple = (0, 0, 0, 0)
    description: str = ""
    snapshot_path: Optional[str] = None
    confirmed: bool = True
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity,
            "track_id": self.track_id,
            "vehicle_class": self.vehicle_class,
            "speed": self.speed,
            "speed_limit": self.speed_limit,
            "timestamp": self.timestamp,
            "location": self.location,
            "bbox": self.bbox,
            "description": self.description,
            "snapshot_path": self.snapshot_path,
            "confirmed": self.confirmed,
        }


class ViolationEngine:
    """
    Central violation detection orchestrator.
    Runs all sub-detectors and aggregates results.
    """
    
    def __init__(self, config: dict = None):
        cfg = config or {}
        
        self.speed_detector = SpeedViolationDetector(
            speed_limit=cfg.get("speed_limit", 60),
            tolerance=cfg.get("speed_tolerance", 5),
        )
        self.red_light_detector = RedLightDetector(
            stop_line_y=cfg.get("stop_line_y", 400),
        )
        self.lane_detector = LaneViolationDetector(
            lane_boundaries=cfg.get("lane_boundaries", [200, 400, 600, 800]),
        )
        self.parking_detector = ParkingViolationDetector(
            max_stationary_seconds=cfg.get("max_stationary", 30),
            forbidden_zones=cfg.get("forbidden_zones", []),
        )
        
        self.violations: List[ViolationRecord] = []
        self._snapshot_dir = Path("data/violations")
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("ViolationEngine initialized with all sub-detectors")
    
    def process(self, tracks: list, frame: np.ndarray) -> List[ViolationRecord]:
        """
        Run all violation checks on current tracked objects.
        
        Returns:
            List of new violations detected this frame
        """
        new_violations = []
        
        for track in tracks:
            # Speed check
            sv = self.speed_detector.check(track)
            if sv:
                record = ViolationRecord(
                    type=ViolationType.SPEED,
                    severity=sv.severity,
                    track_id=sv.track_id,
                    vehicle_class=sv.vehicle_class,
                    speed=sv.speed,
                    speed_limit=sv.speed_limit,
                    location=sv.location,
                    bbox=sv.bbox,
                    description=f"Speed {sv.speed:.1f}km/h (limit {sv.speed_limit}km/h)",
                    snapshot_path=self._save_snapshot(frame, track, "speed"),
                )
                new_violations.append(record)
            
            # Red light check
            rl = self.red_light_detector.check(track)
            if rl:
                record = ViolationRecord(
                    type=ViolationType.RED_LIGHT,
                    severity=rl.severity,
                    track_id=rl.track_id,
                    vehicle_class=rl.vehicle_class,
                    speed=rl.speed,
                    speed_limit=self.speed_detector.speed_limit,
                    location=rl.location,
                    bbox=rl.bbox,
                    description=f"Ran red light at {rl.speed:.1f}km/h",
                    snapshot_path=self._save_snapshot(frame, track, "red_light"),
                )
                new_violations.append(record)
            
            # Lane check
            lv = self.lane_detector.check(track)
            if lv:
                record = ViolationRecord(
                    type=ViolationType.LANE,
                    severity=lv.severity,
                    track_id=lv.track_id,
                    vehicle_class=lv.vehicle_class,
                    location=lv.location,
                    bbox=lv.bbox,
                    description="Illegal lane change detected",
                    snapshot_path=self._save_snapshot(frame, track, "lane"),
                )
                new_violations.append(record)
            
            # Parking check
            pv = self.parking_detector.check(track)
            if pv:
                record = ViolationRecord(
                    type=ViolationType.PARKING,
                    severity=pv.severity,
                    track_id=pv.track_id,
                    vehicle_class=pv.vehicle_class,
                    location=pv.location,
                    bbox=pv.bbox,
                    description=f"Illegal parking for {pv.duration:.0f}s",
                    snapshot_path=self._save_snapshot(frame, track, "parking"),
                )
                new_violations.append(record)
        
        self.violations.extend(new_violations)
        return new_violations
    
    def set_traffic_light(self, state: str):
        """Update traffic light state."""
        self.red_light_detector.set_light_state(state)
    
    def _save_snapshot(self, frame: np.ndarray, track, vtype: str) -> Optional[str]:
        """Save violation evidence frame."""
        try:
            fname = f"{vtype}_{track.track_id}_{int(time.time()*1000)}.jpg"
            path = self._snapshot_dir / fname
            
            img = frame.copy()
            x1, y1, x2, y2 = track.bbox
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(img, f"VIOLATION: {vtype.upper()}", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imwrite(str(path), img)
            return str(path)
        except Exception:
            return None
    
    def get_stats(self) -> dict:
        by_type = {}
        by_severity = {}
        for v in self.violations:
            by_type[v.type.value] = by_type.get(v.type.value, 0) + 1
            by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
        return {
            "total": len(self.violations),
            "by_type": by_type,
            "by_severity": by_severity,
        }
