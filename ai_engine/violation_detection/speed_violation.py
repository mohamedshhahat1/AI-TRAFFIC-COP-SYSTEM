"""
Speed Violation Detector
Detects vehicles exceeding the speed limit.
"""

from dataclasses import dataclass
from typing import Optional
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("speed_violation")
except ImportError:
    from loguru import logger
import time


@dataclass
class SpeedViolation:
    """Speed violation record."""
    track_id: int
    vehicle_class: str
    speed: float
    speed_limit: float
    excess: float
    severity: str
    timestamp: float
    location: tuple
    bbox: tuple


class SpeedViolationDetector:
    """Detects speed limit violations."""
    
    def __init__(self, speed_limit: float = 60.0, tolerance: float = 5.0):
        self.speed_limit = speed_limit
        self.tolerance = tolerance
        self._cooldowns = {}
        self._cooldown_period = 10.0
    
    def check(self, track) -> Optional[SpeedViolation]:
        """
        Check if a tracked vehicle is speeding.
        
        Returns:
            SpeedViolation if detected, None otherwise
        """
        if track.current_speed <= 0:
            return None
        
        threshold = self.speed_limit + self.tolerance
        if track.current_speed <= threshold:
            return None
        
        # Cooldown check
        if self._in_cooldown(track.track_id):
            return None
        
        excess = track.current_speed - self.speed_limit
        severity = self._classify_severity(excess)
        
        violation = SpeedViolation(
            track_id=track.track_id,
            vehicle_class=track.class_name,
            speed=track.current_speed,
            speed_limit=self.speed_limit,
            excess=excess,
            severity=severity,
            timestamp=time.time(),
            location=track.center,
            bbox=track.bbox,
        )
        
        self._set_cooldown(track.track_id)
        logger.warning(
            f"🚨 SPEED: Vehicle #{track.track_id} at {track.current_speed:.1f}km/h "
            f"(limit: {self.speed_limit}) [{severity}]"
        )
        
        return violation
    
    def _classify_severity(self, excess: float) -> str:
        if excess > 40: return "critical"
        if excess > 20: return "high"
        if excess > 10: return "medium"
        return "low"
    
    def _in_cooldown(self, track_id: int) -> bool:
        last = self._cooldowns.get(track_id, 0)
        return (time.time() - last) < self._cooldown_period
    
    def _set_cooldown(self, track_id: int):
        self._cooldowns[track_id] = time.time()
