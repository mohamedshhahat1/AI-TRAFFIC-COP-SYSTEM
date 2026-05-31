"""
Speed Calculator Module
Estimates real-world vehicle speed from tracked pixel positions.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import deque
from loguru import logger
import time


class SpeedCalculator:
    """
    Calculates vehicle speed based on pixel displacement across frames.
    
    Uses perspective transformation and calibration to convert
    pixel movement to real-world speed (km/h).
    """
    
    def __init__(
        self,
        pixel_to_meter_ratio: float = 0.05,
        fps: int = 30,
        speed_limit: float = 60.0,
        smoothing_window: int = 5,
        min_track_length: int = 10
    ):
        """
        Initialize speed calculator.
        
        Args:
            pixel_to_meter_ratio: Conversion factor (meters per pixel)
            fps: Video frames per second
            speed_limit: Speed limit in km/h
            smoothing_window: Number of frames for speed averaging
            min_track_length: Minimum tracked frames before estimating speed
        """
        self.pixel_to_meter = pixel_to_meter_ratio
        self.fps = fps
        self.speed_limit = speed_limit
        self.smoothing_window = smoothing_window
        self.min_track_length = min_track_length
        
        # Speed history per vehicle
        self.speed_history: Dict[int, deque] = {}
        
        # Perspective transform matrix (optional calibration)
        self.perspective_matrix: Optional[np.ndarray] = None
        
        logger.info(
            f"SpeedCalculator initialized: "
            f"ratio={pixel_to_meter_ratio}, fps={fps}, limit={speed_limit}km/h"
        )
    
    def calculate_speed(self, track) -> float:
        """
        Calculate speed for a tracked vehicle.
        
        Args:
            track: Track object with position history
            
        Returns:
            Estimated speed in km/h
        """
        if track.total_frames < self.min_track_length:
            return 0.0
        
        if len(track.positions) < 2:
            return 0.0
        
        # Get recent positions
        positions = track.positions[-self.smoothing_window:]
        timestamps = track.timestamps[-self.smoothing_window:]
        
        if len(positions) < 2 or len(timestamps) < 2:
            return 0.0
        
        # Calculate displacement
        total_displacement = 0.0
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i-1][0]
            dy = positions[i][1] - positions[i-1][1]
            displacement = np.sqrt(dx**2 + dy**2)
            total_displacement += displacement
        
        # Time elapsed
        time_elapsed = timestamps[-1] - timestamps[0]
        
        if time_elapsed <= 0:
            return 0.0
        
        # Convert pixel displacement to meters
        if self.perspective_matrix is not None:
            distance_meters = self._transform_distance(
                positions[0], positions[-1]
            )
        else:
            distance_meters = total_displacement * self.pixel_to_meter
        
        # Calculate speed: meters/second → km/h
        speed_ms = distance_meters / time_elapsed
        speed_kmh = speed_ms * 3.6
        
        # Apply smoothing
        speed_kmh = self._smooth_speed(track.track_id, speed_kmh)
        
        # Update track speed
        track.current_speed = speed_kmh
        track.max_speed = max(track.max_speed, speed_kmh)
        
        # Calculate average speed
        if track.track_id in self.speed_history:
            speeds = list(self.speed_history[track.track_id])
            track.avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
        
        return speed_kmh
    
    def _smooth_speed(self, track_id: int, speed: float) -> float:
        """
        Apply moving average smoothing to speed estimates.
        
        Args:
            track_id: Vehicle track ID
            speed: Raw speed estimate
            
        Returns:
            Smoothed speed value
        """
        if track_id not in self.speed_history:
            self.speed_history[track_id] = deque(maxlen=self.smoothing_window)
        
        self.speed_history[track_id].append(speed)
        
        # Return moving average
        speeds = list(self.speed_history[track_id])
        return sum(speeds) / len(speeds)
    
    def _transform_distance(
        self, 
        point1: Tuple[int, int], 
        point2: Tuple[int, int]
    ) -> float:
        """
        Transform pixel distance using perspective matrix.
        
        Args:
            point1: Start point (x, y)
            point2: End point (x, y)
            
        Returns:
            Real-world distance in meters
        """
        if self.perspective_matrix is None:
            dx = point2[0] - point1[0]
            dy = point2[1] - point1[1]
            return np.sqrt(dx**2 + dy**2) * self.pixel_to_meter
        
        # Transform points using perspective matrix
        pts1 = np.array([[point1]], dtype=np.float32)
        pts2 = np.array([[point2]], dtype=np.float32)
        
        transformed1 = cv2.perspectiveTransform(pts1, self.perspective_matrix)
        transformed2 = cv2.perspectiveTransform(pts2, self.perspective_matrix)
        
        dx = transformed2[0][0][0] - transformed1[0][0][0]
        dy = transformed2[0][0][1] - transformed1[0][0][1]
        
        return np.sqrt(dx**2 + dy**2)
    
    def calibrate(
        self,
        pixel_points: List[Tuple[int, int]],
        real_points: List[Tuple[float, float]]
    ):
        """
        Calibrate the speed calculator using reference points.
        
        Args:
            pixel_points: 4 corner points in pixel coordinates
            real_points: Corresponding 4 corner points in real-world coordinates (meters)
        """
        import cv2
        
        if len(pixel_points) != 4 or len(real_points) != 4:
            logger.error("Calibration requires exactly 4 point pairs")
            return
        
        src = np.array(pixel_points, dtype=np.float32)
        dst = np.array(real_points, dtype=np.float32)
        
        self.perspective_matrix = cv2.getPerspectiveTransform(src, dst)
        
        logger.info("Speed calculator calibrated with perspective transform")
    
    def is_overspeeding(self, track) -> bool:
        """
        Check if a vehicle is exceeding the speed limit.
        
        Args:
            track: Track object
            
        Returns:
            True if vehicle speed exceeds the limit
        """
        return track.current_speed > self.speed_limit
    
    def get_speed_category(self, speed: float) -> str:
        """
        Categorize speed relative to the limit.
        
        Args:
            speed: Vehicle speed in km/h
            
        Returns:
            Category string
        """
        if speed <= 0:
            return "stationary"
        elif speed <= self.speed_limit * 0.5:
            return "slow"
        elif speed <= self.speed_limit:
            return "normal"
        elif speed <= self.speed_limit * 1.2:
            return "above_limit"
        elif speed <= self.speed_limit * 1.5:
            return "speeding"
        else:
            return "dangerous"
    
    def update_all_tracks(self, tracks: list) -> Dict[int, float]:
        """
        Calculate speeds for all active tracks.
        
        Args:
            tracks: List of Track objects
            
        Returns:
            Dictionary mapping track_id to speed
        """
        speeds = {}
        for track in tracks:
            speed = self.calculate_speed(track)
            speeds[track.track_id] = speed
        return speeds
    
    def get_statistics(self) -> dict:
        """Get speed estimation statistics."""
        all_speeds = []
        for speeds in self.speed_history.values():
            all_speeds.extend(list(speeds))
        
        if not all_speeds:
            return {"avg_speed": 0, "max_speed": 0, "vehicles_tracked": 0}
        
        return {
            "avg_speed": sum(all_speeds) / len(all_speeds),
            "max_speed": max(all_speeds),
            "min_speed": min(all_speeds),
            "vehicles_tracked": len(self.speed_history),
            "speed_limit": self.speed_limit,
            "overspeeding_count": sum(
                1 for s in all_speeds if s > self.speed_limit
            ),
        }
    
    def cleanup_track(self, track_id: int):
        """Remove speed history for a deactivated track."""
        if track_id in self.speed_history:
            del self.speed_history[track_id]
