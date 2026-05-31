"""
Parking Violation Detector
Detects vehicles parked in forbidden zones.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("parking_violation")
except ImportError:
    from loguru import logger
import time
import numpy as np
import cv2


@dataclass
class ParkingViolation:
    """Parking violation record."""
    track_id: int
    vehicle_class: str
    duration: float  # seconds stationary
    severity: str
    timestamp: float
    location: tuple
    bbox: tuple


class ParkingViolationDetector:
    """Detects illegal parking in forbidden zones."""
    
    def __init__(
        self,
        max_stationary_seconds: float = 30.0,
        forbidden_zones: List[List[tuple]] = None,
    ):
        self.max_stationary = max_stationary_seconds
        self.forbidden_zones = forbidden_zones or []
        self._stationary_since: Dict[int, float] = {}
        self._cooldowns = {}
        self._cooldown_period = 60.0
    
    def check(self, track) -> Optional[ParkingViolation]:
        """Check if vehicle is illegally parked."""
        # Vehicle is nearly stopped
        if track.current_speed < 2.0:
            if track.track_id not in self._stationary_since:
                self._stationary_since[track.track_id] = time.time()
            
            duration = time.time() - self._stationary_since[track.track_id]
            
            if duration > self.max_stationary:
                if self._in_cooldown(track.track_id):
                    return None
                
                if not self._in_forbidden_zone(track.center):
                    return None
                
                violation = ParkingViolation(
                    track_id=track.track_id,
                    vehicle_class=track.class_name,
                    duration=duration,
                    severity="low",
                    timestamp=time.time(),
                    location=track.center,
                    bbox=track.bbox,
                )
                
                self._set_cooldown(track.track_id)
                logger.warning(
                    f"🚨 PARKING: Vehicle #{track.track_id} stationary for {duration:.0f}s"
                )
                return violation
        else:
            self._stationary_since.pop(track.track_id, None)
        
        return None
    
    def _in_forbidden_zone(self, pos: tuple) -> bool:
        """Check if position falls in a forbidden zone."""
        if not self.forbidden_zones:
            return True  # If no zones defined, all areas are monitored
        
        for zone in self.forbidden_zones:
            if len(zone) >= 3:
                pts = np.array(zone, dtype=np.int32)
                if cv2.pointPolygonTest(pts, pos, False) >= 0:
                    return True
        return False
    
    def _in_cooldown(self, track_id: int) -> bool:
        return (time.time() - self._cooldowns.get(track_id, 0)) < self._cooldown_period
    
    def _set_cooldown(self, track_id: int):
        self._cooldowns[track_id] = time.time()
