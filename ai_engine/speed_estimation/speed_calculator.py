"""
Speed Calculator Module
Estimates vehicle speed from pixel displacement and calibration data.
"""

import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional
from collections import deque
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("speed_calculator")
except ImportError:
    from loguru import logger


class SpeedCalculator:
    """
    Calculates real-world vehicle speed from tracked positions.
    Converts pixel movement to km/h using calibration factors.

    pixel_to_meter and fps should be configured per camera via camera_config.yaml.
    """

    def __init__(
        self,
        pixel_to_meter: float = 0.05,
        fps: int = 30,
        speed_limit: float = 60.0,
        smoothing_window: int = 5,
        min_track_frames: int = 10,
    ):
        self.pixel_to_meter = pixel_to_meter
        self.fps = fps
        self.speed_limit = speed_limit
        self.smoothing_window = smoothing_window
        self.min_track_frames = min_track_frames

        self._speed_history: Dict[int, deque] = {}
        self._perspective_matrix: Optional[np.ndarray] = None
        self._is_calibrated = False

        logger.info(f"SpeedCalculator | limit={speed_limit}km/h | ratio={pixel_to_meter} | fps={fps}")

    @classmethod
    def from_config(cls, camera_config: dict, defaults: dict = None) -> "SpeedCalculator":
        """
        Create a SpeedCalculator from camera configuration.

        Args:
            camera_config: Per-camera config with pixel_to_meter, fps, speed_limit
            defaults: Fallback values if not specified in camera config
        """
        defaults = defaults or {}
        return cls(
            pixel_to_meter=camera_config.get("pixel_to_meter", defaults.get("pixel_to_meter", 0.05)),
            fps=camera_config.get("fps", defaults.get("fps", 30)),
            speed_limit=camera_config.get("speed_limit", defaults.get("speed_limit", 60.0)),
            smoothing_window=camera_config.get("smoothing_window", defaults.get("smoothing_window", 5)),
            min_track_frames=camera_config.get("min_track_frames", defaults.get("min_track_frames", 10)),
        )

    def update_fps(self, fps: int):
        """Update FPS (e.g., from actual video metadata)."""
        if fps > 0:
            self.fps = fps
            logger.info(f"SpeedCalculator FPS updated to {fps}")
    
    def calculate(self, track) -> float:
        """
        Calculate speed for a tracked object.
        
        Args:
            track: TrackedObject with position history
            
        Returns:
            Speed in km/h
        """
        if track.frames_tracked < self.min_track_frames:
            return 0.0
        if len(track.positions) < 2 or len(track.timestamps) < 2:
            return 0.0
        
        positions = track.positions[-self.smoothing_window:]
        timestamps = track.timestamps[-self.smoothing_window:]
        
        if len(positions) < 2:
            return 0.0
        
        # Total pixel displacement
        total_px = 0.0
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i-1][0]
            dy = positions[i][1] - positions[i-1][1]
            total_px += np.sqrt(dx**2 + dy**2)
        
        # Time elapsed
        dt = timestamps[-1] - timestamps[0]
        if dt <= 0:
            return 0.0
        
        # Convert to real distance (use perspective transform if calibrated)
        if self._perspective_matrix is not None:
            start_pt = np.array([[positions[0]]], dtype=np.float32)
            end_pt = np.array([[positions[-1]]], dtype=np.float32)
            t_start_pt = cv2.perspectiveTransform(start_pt, self._perspective_matrix)
            t_end_pt = cv2.perspectiveTransform(end_pt, self._perspective_matrix)
            dx = t_end_pt[0][0][0] - t_start_pt[0][0][0]
            dy = t_end_pt[0][0][1] - t_start_pt[0][0][1]
            distance_m = np.sqrt(dx**2 + dy**2)
        else:
            distance_m = total_px * self.pixel_to_meter
        
        # Speed: m/s → km/h
        speed_ms = distance_m / dt
        speed_kmh = speed_ms * 3.6
        
        # Smooth
        speed_kmh = self._smooth(track.track_id, speed_kmh)
        
        # Update track
        track.current_speed = speed_kmh
        track.max_speed = max(track.max_speed, speed_kmh)
        
        if track.track_id in self._speed_history:
            speeds = list(self._speed_history[track.track_id])
            track.avg_speed = sum(speeds) / len(speeds)
        
        return speed_kmh
    
    def _smooth(self, track_id: int, speed: float) -> float:
        """Moving average smoothing."""
        if track_id not in self._speed_history:
            self._speed_history[track_id] = deque(maxlen=self.smoothing_window)
        self._speed_history[track_id].append(speed)
        vals = list(self._speed_history[track_id])
        return sum(vals) / len(vals)
    
    def calibrate(self, pixel_pts: List[Tuple], real_pts: List[Tuple]):
        """Set perspective transform for accurate measurement."""
        src = np.array(pixel_pts, dtype=np.float32)
        dst = np.array(real_pts, dtype=np.float32)
        self._perspective_matrix = cv2.getPerspectiveTransform(src, dst)
        self._is_calibrated = True
        logger.info("Speed calculator calibrated with perspective transform")

    @property
    def is_calibrated(self) -> bool:
        """Whether camera calibration has been applied."""
        return self._is_calibrated
    
    def is_overspeeding(self, track) -> bool:
        """Check if vehicle exceeds speed limit."""
        return track.current_speed > self.speed_limit
    
    def get_category(self, speed: float) -> str:
        """Categorize speed."""
        if speed <= 0: return "stationary"
        if speed <= self.speed_limit * 0.5: return "slow"
        if speed <= self.speed_limit: return "normal"
        if speed <= self.speed_limit * 1.2: return "above_limit"
        if speed <= self.speed_limit * 1.5: return "speeding"
        return "dangerous"
    
    def update_all(self, tracks: list) -> Dict[int, float]:
        """Calculate speed for all tracks."""
        return {t.track_id: self.calculate(t) for t in tracks}
    
    def cleanup(self, track_id: int):
        """Remove history for dead track."""
        self._speed_history.pop(track_id, None)
