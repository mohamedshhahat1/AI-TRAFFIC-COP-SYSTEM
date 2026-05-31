"""
Violation Detector Module
Core engine for detecting various traffic violations in real-time.
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from loguru import logger
import time
from pathlib import Path

from .violation import Violation, ViolationType, Severity


class ViolationDetector:
    """
    Detects traffic violations based on tracked vehicle data.
    
    Supports:
    - Speed violations
    - Red light violations
    - Lane violations
    - Illegal parking
    - Wrong way driving
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize violation detector.
        
        Args:
            config: Configuration dictionary for violation parameters
        """
        self.config = config or self._default_config()
        
        # Violation tracking
        self.violations: List[Violation] = []
        self.violation_cooldown: Dict[int, Dict[str, float]] = {}
        self.cooldown_period = 10.0  # seconds between same violation for same vehicle
        
        # Parking detection state
        self.stationary_vehicles: Dict[int, float] = {}  # track_id -> stationary_since
        
        # Traffic light state
        self.traffic_light_state: str = "unknown"  # red, green, yellow, unknown
        self.crossing_line_y: int = self.config.get("red_light", {}).get(
            "crossing_line_y", 400
        )
        
        # Lane boundaries
        self.lane_boundaries: List[int] = self.config.get("lane", {}).get(
            "lane_boundaries", [200, 400, 600, 800]
        )
        
        # Snapshot directory
        self.snapshot_dir = Path("data/violations")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("ViolationDetector initialized")
    
    def _default_config(self) -> dict:
        """Return default violation detection configuration."""
        return {
            "speed": {
                "enabled": True,
                "limit": 60,
                "tolerance": 5,
            },
            "red_light": {
                "enabled": True,
                "crossing_line_y": 400,
            },
            "lane": {
                "enabled": True,
                "lane_boundaries": [200, 400, 600, 800],
            },
            "parking": {
                "enabled": True,
                "max_stationary_time": 30,
                "forbidden_zones": [],
            },
        }
    
    def detect_violations(
        self, 
        tracks: list, 
        frame: np.ndarray,
        detections: list = None
    ) -> List[Violation]:
        """
        Run all violation detection checks on current frame.
        
        Args:
            tracks: List of active Track objects
            frame: Current video frame
            detections: Raw detections (for traffic light state)
            
        Returns:
            List of new violations detected this frame
        """
        new_violations = []
        
        for track in tracks:
            # Speed violation
            if self.config["speed"]["enabled"]:
                violation = self._check_speed_violation(track, frame)
                if violation:
                    new_violations.append(violation)
            
            # Red light violation
            if self.config["red_light"]["enabled"]:
                violation = self._check_red_light_violation(track, frame)
                if violation:
                    new_violations.append(violation)
            
            # Lane violation
            if self.config["lane"]["enabled"]:
                violation = self._check_lane_violation(track, frame)
                if violation:
                    new_violations.append(violation)
            
            # Illegal parking
            if self.config["parking"]["enabled"]:
                violation = self._check_parking_violation(track, frame)
                if violation:
                    new_violations.append(violation)
        
        # Add new violations to history
        self.violations.extend(new_violations)
        
        return new_violations
    
    def _check_speed_violation(
        self, track, frame: np.ndarray
    ) -> Optional[Violation]:
        """Check if vehicle is exceeding speed limit."""
        speed_limit = self.config["speed"]["limit"]
        tolerance = self.config["speed"]["tolerance"]
        
        if track.current_speed <= 0:
            return None
        
        if track.current_speed > (speed_limit + tolerance):
            # Check cooldown
            if self._is_in_cooldown(track.track_id, "speed"):
                return None
            
            # Determine severity
            excess = track.current_speed - speed_limit
            if excess > 40:
                severity = Severity.CRITICAL
            elif excess > 20:
                severity = Severity.HIGH
            elif excess > 10:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW
            
            # Save frame snapshot
            snapshot_path = self._save_snapshot(frame, track, "speed")
            
            violation = Violation(
                violation_type=ViolationType.SPEED,
                severity=severity,
                track_id=track.track_id,
                vehicle_class=track.class_name,
                location=track.center,
                bbox=track.bbox,
                speed=track.current_speed,
                speed_limit=speed_limit,
                confidence=min(track.confidence, 0.95),
                description=(
                    f"Vehicle {track.track_id} ({track.class_name}) "
                    f"detected at {track.current_speed:.1f} km/h "
                    f"(limit: {speed_limit} km/h)"
                ),
                frame_snapshot=snapshot_path,
                is_confirmed=True,
            )
            
            self._set_cooldown(track.track_id, "speed")
            logger.warning(f"🚨 Speed violation: {violation.description}")
            
            return violation
        
        return None
    
    def _check_red_light_violation(
        self, track, frame: np.ndarray
    ) -> Optional[Violation]:
        """Check if vehicle crosses during red light."""
        if self.traffic_light_state != "red":
            return None
        
        # Check if vehicle crossed the stop line
        if len(track.positions) < 2:
            return None
        
        prev_y = track.positions[-2][1]
        curr_y = track.positions[-1][1]
        
        # Vehicle crossed from above to below the line
        if prev_y < self.crossing_line_y <= curr_y:
            if self._is_in_cooldown(track.track_id, "red_light"):
                return None
            
            snapshot_path = self._save_snapshot(frame, track, "red_light")
            
            violation = Violation(
                violation_type=ViolationType.RED_LIGHT,
                severity=Severity.HIGH,
                track_id=track.track_id,
                vehicle_class=track.class_name,
                location=track.center,
                bbox=track.bbox,
                speed=track.current_speed,
                confidence=0.85,
                description=(
                    f"Vehicle {track.track_id} ({track.class_name}) "
                    f"ran red light at speed {track.current_speed:.1f} km/h"
                ),
                frame_snapshot=snapshot_path,
                is_confirmed=True,
            )
            
            self._set_cooldown(track.track_id, "red_light")
            logger.warning(f"🚨 Red light violation: {violation.description}")
            
            return violation
        
        return None
    
    def _check_lane_violation(
        self, track, frame: np.ndarray
    ) -> Optional[Violation]:
        """Check if vehicle makes illegal lane change."""
        if len(track.positions) < 10:
            return None
        
        # Detect rapid lateral movement (lane change)
        recent_positions = track.positions[-10:]
        x_positions = [p[0] for p in recent_positions]
        
        # Check if vehicle crossed a lane boundary
        for boundary in self.lane_boundaries:
            crossings = 0
            for i in range(1, len(x_positions)):
                if (x_positions[i-1] < boundary <= x_positions[i] or
                    x_positions[i-1] > boundary >= x_positions[i]):
                    crossings += 1
            
            # Multiple crossings in short time = erratic driving
            if crossings >= 2:
                if self._is_in_cooldown(track.track_id, "lane"):
                    return None
                
                snapshot_path = self._save_snapshot(frame, track, "lane")
                
                violation = Violation(
                    violation_type=ViolationType.LANE,
                    severity=Severity.MEDIUM,
                    track_id=track.track_id,
                    vehicle_class=track.class_name,
                    location=track.center,
                    bbox=track.bbox,
                    speed=track.current_speed,
                    confidence=0.7,
                    description=(
                        f"Vehicle {track.track_id} ({track.class_name}) "
                        f"made illegal lane change"
                    ),
                    frame_snapshot=snapshot_path,
                    is_confirmed=True,
                )
                
                self._set_cooldown(track.track_id, "lane")
                logger.warning(f"🚨 Lane violation: {violation.description}")
                
                return violation
        
        return None
    
    def _check_parking_violation(
        self, track, frame: np.ndarray
    ) -> Optional[Violation]:
        """Check if vehicle is illegally parked."""
        max_stationary = self.config["parking"]["max_stationary_time"]
        
        # Check if vehicle is stationary
        if track.current_speed < 2.0:  # Nearly stopped
            if track.track_id not in self.stationary_vehicles:
                self.stationary_vehicles[track.track_id] = time.time()
            
            stationary_duration = time.time() - self.stationary_vehicles[track.track_id]
            
            if stationary_duration > max_stationary:
                if self._is_in_cooldown(track.track_id, "parking"):
                    return None
                
                # Check if in forbidden zone
                in_forbidden = self._is_in_forbidden_zone(track.center)
                
                if in_forbidden:
                    snapshot_path = self._save_snapshot(frame, track, "parking")
                    
                    violation = Violation(
                        violation_type=ViolationType.ILLEGAL_PARKING,
                        severity=Severity.LOW,
                        track_id=track.track_id,
                        vehicle_class=track.class_name,
                        location=track.center,
                        bbox=track.bbox,
                        confidence=0.8,
                        description=(
                            f"Vehicle {track.track_id} ({track.class_name}) "
                            f"parked illegally for {stationary_duration:.0f}s"
                        ),
                        frame_snapshot=snapshot_path,
                        is_confirmed=True,
                    )
                    
                    self._set_cooldown(track.track_id, "parking")
                    logger.warning(f"🚨 Parking violation: {violation.description}")
                    
                    return violation
        else:
            # Vehicle is moving, reset stationary timer
            if track.track_id in self.stationary_vehicles:
                del self.stationary_vehicles[track.track_id]
        
        return None
    
    def _is_in_forbidden_zone(self, position: Tuple[int, int]) -> bool:
        """Check if position is in a forbidden parking zone."""
        forbidden_zones = self.config["parking"].get("forbidden_zones", [])
        
        if not forbidden_zones:
            return True  # If no zones defined, anywhere is forbidden
        
        for zone in forbidden_zones:
            if len(zone) >= 3:
                zone_array = np.array(zone, dtype=np.int32)
                result = cv2.pointPolygonTest(zone_array, position, False)
                if result >= 0:
                    return True
        
        return False
    
    def update_traffic_light_state(self, state: str):
        """
        Update the current traffic light state.
        
        Args:
            state: Traffic light state (red, green, yellow, unknown)
        """
        self.traffic_light_state = state
    
    def _is_in_cooldown(self, track_id: int, violation_type: str) -> bool:
        """Check if a violation type is in cooldown for a track."""
        if track_id not in self.violation_cooldown:
            return False
        
        if violation_type not in self.violation_cooldown[track_id]:
            return False
        
        elapsed = time.time() - self.violation_cooldown[track_id][violation_type]
        return elapsed < self.cooldown_period
    
    def _set_cooldown(self, track_id: int, violation_type: str):
        """Set cooldown for a violation type on a track."""
        if track_id not in self.violation_cooldown:
            self.violation_cooldown[track_id] = {}
        self.violation_cooldown[track_id][violation_type] = time.time()
    
    def _save_snapshot(
        self, 
        frame: np.ndarray, 
        track, 
        violation_type: str
    ) -> Optional[str]:
        """Save violation frame as evidence."""
        try:
            timestamp = int(time.time() * 1000)
            filename = f"{violation_type}_{track.track_id}_{timestamp}.jpg"
            filepath = self.snapshot_dir / filename
            
            # Draw violation info on frame
            annotated = frame.copy()
            x1, y1, x2, y2 = track.bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(
                annotated,
                f"VIOLATION: {violation_type.upper()}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 0, 255), 2
            )
            
            cv2.imwrite(str(filepath), annotated)
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return None
    
    def get_violations(
        self, 
        violation_type: Optional[ViolationType] = None,
        severity: Optional[Severity] = None,
        limit: int = 50
    ) -> List[Violation]:
        """
        Get violations with optional filtering.
        
        Args:
            violation_type: Filter by violation type
            severity: Filter by severity
            limit: Maximum number of violations to return
            
        Returns:
            Filtered list of violations
        """
        filtered = self.violations
        
        if violation_type:
            filtered = [v for v in filtered if v.violation_type == violation_type]
        
        if severity:
            filtered = [v for v in filtered if v.severity == severity]
        
        return filtered[-limit:]
    
    def get_statistics(self) -> dict:
        """Get violation statistics."""
        stats = {
            "total_violations": len(self.violations),
            "by_type": {},
            "by_severity": {},
            "recent_violations": len([
                v for v in self.violations 
                if time.time() - v.timestamp < 3600
            ]),
        }
        
        for vtype in ViolationType:
            count = len([v for v in self.violations if v.violation_type == vtype])
            if count > 0:
                stats["by_type"][vtype.value] = count
        
        for sev in Severity:
            count = len([v for v in self.violations if v.severity == sev])
            if count > 0:
                stats["by_severity"][sev.value] = count
        
        return stats
    
    def clear_violations(self):
        """Clear all violation records."""
        self.violations.clear()
        self.violation_cooldown.clear()
        self.stationary_vehicles.clear()
        logger.info("All violations cleared")
