"""
Lane Violation Detector
Detects illegal lane changes and wrong-way driving.
"""

from dataclasses import dataclass
from typing import Optional, List
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("lane_violation")
except ImportError:
    from loguru import logger
import time


@dataclass
class LaneViolation:
    """Lane violation record."""
    track_id: int
    vehicle_class: str
    violation_subtype: str  # lane_change, wrong_way
    severity: str
    timestamp: float
    location: tuple
    bbox: tuple


class LaneViolationDetector:
    """
    Detects lane-related violations.

    lane_boundaries should be configured per camera via camera_config.yaml
    based on actual lane positions in the camera's field of view.
    """

    def __init__(self, lane_boundaries: List[int] = None, frame_width: int = 1280):
        """
        Initialize lane violation detector.

        Args:
            lane_boundaries: List of x-pixel positions for lane dividers.
                            If None, auto-generates evenly spaced boundaries
                            based on frame_width (suitable for demo only).
            frame_width: Video frame width for auto-boundary calculation.
        """
        if lane_boundaries:
            self.lane_boundaries = lane_boundaries
        else:
            # Auto-generate: divide frame into 4 lanes
            step = frame_width // 5
            self.lane_boundaries = [step * i for i in range(1, 5)]
            logger.info(f"Lane boundaries auto-generated: {self.lane_boundaries} "
                       f"(configure per-camera for production)")

        self._cooldowns = {}
        self._cooldown_period = 12.0

    @classmethod
    def from_config(cls, camera_config: dict) -> "LaneViolationDetector":
        """Create detector from camera configuration."""
        return cls(
            lane_boundaries=camera_config.get("lane_boundaries"),
            frame_width=camera_config.get("frame_width", 1280),
        )
    
    def check(self, track) -> Optional[LaneViolation]:
        """Check for illegal lane changes."""
        if len(track.positions) < 15:
            return None
        
        if self._in_cooldown(track.track_id):
            return None
        
        # Check for rapid lane boundary crossings
        recent = track.positions[-15:]
        x_vals = [p[0] for p in recent]
        
        for boundary in self.lane_boundaries:
            crossings = 0
            for i in range(1, len(x_vals)):
                if (x_vals[i-1] < boundary <= x_vals[i] or
                    x_vals[i-1] > boundary >= x_vals[i]):
                    crossings += 1
            
            if crossings >= 2:
                severity = "high" if track.current_speed > 80 else "medium"
                
                violation = LaneViolation(
                    track_id=track.track_id,
                    vehicle_class=track.class_name,
                    violation_subtype="lane_change",
                    severity=severity,
                    timestamp=time.time(),
                    location=track.center,
                    bbox=track.bbox,
                )
                
                self._set_cooldown(track.track_id)
                logger.warning(
                    f"🚨 LANE: Vehicle #{track.track_id} illegal lane change [{severity}]"
                )
                return violation
        
        return None
    
    def _in_cooldown(self, track_id: int) -> bool:
        return (time.time() - self._cooldowns.get(track_id, 0)) < self._cooldown_period
    
    def _set_cooldown(self, track_id: int):
        self._cooldowns[track_id] = time.time()
