"""
Collision Risk Prediction (TTC) Module
Uses vehicle trajectories, speeds, and proximity to predict potential collisions.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("accident_predictor")
except ImportError:
    from loguru import logger
import time


@dataclass
class AccidentRisk:
    """Predicted accident risk assessment."""
    risk_level: str  # low, medium, high, imminent
    risk_score: float  # 0.0 - 1.0
    involved_vehicles: List[int]
    predicted_collision_point: Optional[Tuple[int, int]]
    time_to_collision: float  # seconds
    description: str
    timestamp: float


class AccidentPredictor:
    """
    AI-powered accident prediction engine.
    
    Analyzes:
    - Vehicle trajectories and projected paths
    - Relative speeds between nearby vehicles
    - Time-to-collision (TTC) calculations
    - Dangerous driving patterns (sudden braking, swerving)
    """
    
    def __init__(
        self,
        min_ttc_warning: float = 3.0,     # seconds
        min_ttc_critical: float = 1.5,     # seconds
        proximity_threshold: float = 100,   # pixels
        prediction_horizon: int = 30,       # frames ahead
    ):
        self.min_ttc_warning = min_ttc_warning
        self.min_ttc_critical = min_ttc_critical
        self.proximity_threshold = proximity_threshold
        self.prediction_horizon = prediction_horizon
        
        self.risk_history: List[AccidentRisk] = []  # Pruned periodically
        self._alerts_sent: Dict[str, float] = {}
        self._prev_speeds: Dict[int, float] = {}  # track_id -> previous speed
        
        logger.info("AccidentPredictor initialized")
    
    def analyze(self, tracks: list) -> List[AccidentRisk]:
        """
        Analyze all tracked vehicles for collision risk.
        
        Args:
            tracks: List of active TrackedObject instances
            
        Returns:
            List of identified accident risks
        """
        risks = []
        
        if len(tracks) < 2:
            return risks
        
        # Check all vehicle pairs
        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                risk = self._assess_pair(tracks[i], tracks[j])
                if risk:
                    risks.append(risk)
        
        # Check for dangerous individual behavior
        for track in tracks:
            risk = self._check_dangerous_behavior(track)
            if risk:
                risks.append(risk)
        
        self.risk_history.extend(risks)
        # Prune old entries (keep last 500)
        if len(self.risk_history) > 500:
            self.risk_history = self.risk_history[-500:]
        return risks
    
    def _assess_pair(self, track_a, track_b) -> Optional[AccidentRisk]:
        """Assess collision risk between two vehicles."""
        # Current distance
        dist = self._distance(track_a.center, track_b.center)
        
        if dist > self.proximity_threshold * 3:
            return None  # Too far apart
        
        # Predict future positions
        pos_a = self._predict_position(track_a)
        pos_b = self._predict_position(track_b)
        
        if pos_a is None or pos_b is None:
            return None
        
        # Calculate time-to-collision
        ttc = self._calculate_ttc(track_a, track_b)
        
        if ttc is None or ttc > self.min_ttc_warning:
            return None
        
        # Future distance
        future_dist = self._distance(pos_a, pos_b)
        
        # Risk scoring
        risk_score = self._compute_risk_score(dist, future_dist, ttc, track_a, track_b)
        
        if risk_score < 0.3:
            return None
        
        # Determine risk level
        if ttc < self.min_ttc_critical:
            level = "imminent"
        elif risk_score > 0.7:
            level = "high"
        elif risk_score > 0.5:
            level = "medium"
        else:
            level = "low"
        
        # Predict collision point
        collision_pt = (
            (pos_a[0] + pos_b[0]) // 2,
            (pos_a[1] + pos_b[1]) // 2,
        )
        
        risk = AccidentRisk(
            risk_level=level,
            risk_score=risk_score,
            involved_vehicles=[track_a.track_id, track_b.track_id],
            predicted_collision_point=collision_pt,
            time_to_collision=ttc,
            description=(
                f"Potential collision: Vehicle #{track_a.track_id} "
                f"and #{track_b.track_id} | TTC: {ttc:.1f}s"
            ),
            timestamp=time.time(),
        )
        
        if level in ("high", "imminent"):
            logger.warning(f"⚠️ ACCIDENT RISK [{level}]: {risk.description}")
        
        return risk
    
    def _check_dangerous_behavior(self, track) -> Optional[AccidentRisk]:
        """Detect dangerous individual driving patterns."""
        if len(track.positions) < 10:
            return None
        
        # Detect sudden deceleration (hard braking)
        if track.track_id in self._prev_speeds:
            speed_change = self._prev_speeds[track.track_id] - track.current_speed
            if speed_change > 30:  # Sudden 30km/h drop
                self._prev_speeds[track.track_id] = track.current_speed
                return AccidentRisk(
                    risk_level="medium",
                    risk_score=0.6,
                    involved_vehicles=[track.track_id],
                    predicted_collision_point=None,
                    time_to_collision=float('inf'),
                    description=f"Hard braking detected: Vehicle #{track.track_id}",
                    timestamp=time.time(),
                )
        
        self._prev_speeds[track.track_id] = track.current_speed
        
        # Detect swerving (erratic lateral movement)
        recent_x = [p[0] for p in track.positions[-10:]]
        if len(recent_x) >= 10:
            x_std = np.std(recent_x)
            if x_std > 50:  # High lateral variance
                return AccidentRisk(
                    risk_level="medium",
                    risk_score=0.5,
                    involved_vehicles=[track.track_id],
                    predicted_collision_point=None,
                    time_to_collision=float('inf'),
                    description=f"Erratic driving: Vehicle #{track.track_id}",
                    timestamp=time.time(),
                )
        
        return None
    
    def _predict_position(self, track) -> Optional[Tuple[int, int]]:
        """Linear extrapolation of future position."""
        if len(track.positions) < 5:
            return None
        
        recent = track.positions[-5:]
        dx = (recent[-1][0] - recent[0][0]) / len(recent)
        dy = (recent[-1][1] - recent[0][1]) / len(recent)
        
        future_x = int(recent[-1][0] + dx * self.prediction_horizon)
        future_y = int(recent[-1][1] + dy * self.prediction_horizon)
        
        return (future_x, future_y)
    
    def _calculate_ttc(self, track_a, track_b) -> Optional[float]:
        """Calculate time-to-collision between two vehicles."""
        if len(track_a.positions) < 3 or len(track_b.positions) < 3:
            return None
        
        # Current positions and velocities
        pa = np.array(track_a.center, dtype=float)
        pb = np.array(track_b.center, dtype=float)
        
        va = np.array(track_a.positions[-1], dtype=float) - np.array(track_a.positions[-3], dtype=float)
        vb = np.array(track_b.positions[-1], dtype=float) - np.array(track_b.positions[-3], dtype=float)
        
        # Relative position and velocity
        dp = pb - pa
        dv = vb - va
        
        # Time to minimum distance
        dv_sq = np.dot(dv, dv)
        if dv_sq < 1e-6:
            return None
        
        t_min = -np.dot(dp, dv) / dv_sq
        
        if t_min < 0:
            return None  # Already diverging
        
        # t_min is in frame units; convert to seconds (assuming ~30fps)
        ttc_seconds = t_min / 30.0
        
        return ttc_seconds
    
    def _compute_risk_score(self, dist, future_dist, ttc, track_a, track_b) -> float:
        """Compute overall risk score 0-1."""
        score = 0.0
        
        # Proximity factor
        if dist < self.proximity_threshold:
            score += 0.3 * (1 - dist / self.proximity_threshold)
        
        # Convergence factor
        if future_dist < dist:
            score += 0.3 * (1 - future_dist / max(dist, 1))
        
        # TTC factor
        if ttc < self.min_ttc_warning:
            score += 0.4 * (1 - ttc / self.min_ttc_warning)
        
        # Speed amplifier
        combined_speed = track_a.current_speed + track_b.current_speed
        if combined_speed > 100:
            score *= 1.2
        
        return min(1.0, score)
    
    def _distance(self, p1: tuple, p2: tuple) -> float:
        return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5
    
    def get_current_risks(self, min_level: str = "medium") -> List[AccidentRisk]:
        """Get recent risks above threshold."""
        levels = {"low": 0, "medium": 1, "high": 2, "imminent": 3}
        min_val = levels.get(min_level, 1)
        
        recent = [
            r for r in self.risk_history
            if time.time() - r.timestamp < 30 and levels.get(r.risk_level, 0) >= min_val
        ]
        return recent
    
    def get_stats(self) -> dict:
        return {
            "total_risks_detected": len(self.risk_history),
            "current_active": len(self.get_current_risks("low")),
            "imminent_risks": len([r for r in self.risk_history if r.risk_level == "imminent"]),
        }
