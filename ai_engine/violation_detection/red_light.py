"""
Red Light Violation Detector
Detects vehicles running red traffic lights.
"""

from dataclasses import dataclass
from typing import Optional
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("red_light")
except ImportError:
    from loguru import logger
import time


@dataclass
class RedLightViolation:
    """Red light violation record."""
    track_id: int
    vehicle_class: str
    speed: float
    severity: str
    timestamp: float
    location: tuple
    bbox: tuple


class RedLightDetector:
    """Detects red light running violations."""
    
    def __init__(self, stop_line_y: int = 400):
        self.stop_line_y = stop_line_y
        self.traffic_light_state = "unknown"
        self._cooldowns = {}
        self._cooldown_period = 15.0
    
    def set_light_state(self, state: str):
        """Update traffic light state: red, green, yellow, unknown."""
        self.traffic_light_state = state
    
    def check(self, track) -> Optional[RedLightViolation]:
        """Check if vehicle crossed stop line during red."""
        if self.traffic_light_state != "red":
            return None
        
        if len(track.positions) < 2:
            return None
        
        prev_y = track.positions[-2][1]
        curr_y = track.positions[-1][1]
        
        # Crossed stop line (going downward in frame)
        if prev_y < self.stop_line_y <= curr_y:
            if self._in_cooldown(track.track_id):
                return None
            
            severity = "critical" if track.current_speed > 50 else "high"
            
            violation = RedLightViolation(
                track_id=track.track_id,
                vehicle_class=track.class_name,
                speed=track.current_speed,
                severity=severity,
                timestamp=time.time(),
                location=track.center,
                bbox=track.bbox,
            )
            
            self._set_cooldown(track.track_id)
            logger.warning(
                f"🚨 RED LIGHT: Vehicle #{track.track_id} crossed at "
                f"{track.current_speed:.1f}km/h [{severity}]"
            )
            
            return violation
        
        return None
    
    def _in_cooldown(self, track_id: int) -> bool:
        return (time.time() - self._cooldowns.get(track_id, 0)) < self._cooldown_period
    
    def _set_cooldown(self, track_id: int):
        self._cooldowns[track_id] = time.time()
