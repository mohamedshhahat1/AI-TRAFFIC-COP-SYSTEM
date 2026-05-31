"""
Traffic Congestion Analyzer
AI-powered traffic density and congestion prediction.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import deque
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("congestion_analyzer")
except ImportError:
    from loguru import logger
import time


@dataclass
class CongestionReport:
    """Traffic congestion status report."""
    level: str           # free, moderate, heavy, gridlock
    density: float       # vehicles per unit area
    avg_speed: float     # km/h
    flow_rate: float     # vehicles/minute
    prediction: str      # improving, stable, worsening
    timestamp: float


class CongestionAnalyzer:
    """
    Analyzes real-time traffic congestion levels and predicts trends.
    
    Features:
    - Vehicle density calculation
    - Average speed monitoring
    - Traffic flow rate estimation
    - Congestion trend prediction
    - Peak hour detection
    """
    
    def __init__(
        self,
        roi_area: float = 1000.0,      # monitoring area in sq meters
        free_flow_speed: float = 60.0,  # km/h
        history_window: int = 300,       # seconds of history to keep
    ):
        self.roi_area = roi_area
        self.free_flow_speed = free_flow_speed
        self.history_window = history_window
        
        # Time-series data
        self._density_history: deque = deque(maxlen=history_window)
        self._speed_history: deque = deque(maxlen=history_window)
        self._flow_history: deque = deque(maxlen=history_window)
        self._timestamps: deque = deque(maxlen=history_window)
        
        # Vehicle counting
        self._entry_count = 0
        self._exit_count = 0
        self._last_count_reset = time.time()
        self._seen_entry_ids: set = set()  # Prevent double-counting
        
        logger.info(f"CongestionAnalyzer | area={roi_area}m² | free_flow={free_flow_speed}km/h")
    
    def analyze(self, tracks: list) -> CongestionReport:
        """
        Analyze current congestion state.
        
        Args:
            tracks: List of active tracked vehicles
            
        Returns:
            CongestionReport with current status
        """
        now = time.time()
        
        # Calculate metrics
        density = len(tracks) / self.roi_area * 1000  # vehicles per km
        avg_speed = self._calc_avg_speed(tracks)
        flow_rate = self._calc_flow_rate(tracks)
        
        # Store history
        self._density_history.append(density)
        self._speed_history.append(avg_speed)
        self._flow_history.append(flow_rate)
        self._timestamps.append(now)
        
        # Determine congestion level
        level = self._classify_congestion(density, avg_speed)
        
        # Predict trend
        prediction = self._predict_trend()
        
        report = CongestionReport(
            level=level,
            density=round(density, 2),
            avg_speed=round(avg_speed, 1),
            flow_rate=round(flow_rate, 1),
            prediction=prediction,
            timestamp=now,
        )
        
        return report
    
    def _calc_avg_speed(self, tracks: list) -> float:
        """Calculate average speed of all vehicles."""
        speeds = [t.current_speed for t in tracks if t.current_speed > 0]
        return sum(speeds) / len(speeds) if speeds else 0.0
    
    def _calc_flow_rate(self, tracks: list) -> float:
        """Estimate vehicles per minute flowing through."""
        elapsed = time.time() - self._last_count_reset
        if elapsed < 1:
            return 0.0
        
        # Count vehicles that have been active briefly (just entered) - deduplicated
        new_vehicles = 0
        for t in tracks:
            if t.duration < 2.0 and t.track_id not in self._seen_entry_ids:
                new_vehicles += 1
                self._seen_entry_ids.add(t.track_id)
        
        # Reset every minute
        if elapsed >= 60:
            rate = self._entry_count
            self._entry_count = new_vehicles
            self._last_count_reset = time.time()
            return rate
        
        self._entry_count += new_vehicles
        return self._entry_count / (elapsed / 60)
    
    def _classify_congestion(self, density: float, avg_speed: float) -> str:
        """
        Classify congestion level based on speed and density.
        
        Uses Level of Service (LOS) inspired classification:
        - Free: Speed > 80% of free flow
        - Moderate: Speed 50-80% of free flow
        - Heavy: Speed 25-50% of free flow
        - Gridlock: Speed < 25% of free flow
        """
        speed_ratio = avg_speed / self.free_flow_speed if self.free_flow_speed > 0 else 0
        
        if speed_ratio > 0.8 and density < 20:
            return "free"
        elif speed_ratio > 0.5:
            return "moderate"
        elif speed_ratio > 0.25:
            return "heavy"
        else:
            return "gridlock"
    
    def _predict_trend(self) -> str:
        """
        Predict congestion trend using recent history.
        Simple linear regression on density values.
        """
        if len(self._density_history) < 10:
            return "stable"
        
        recent = list(self._density_history)[-30:]
        
        if len(recent) < 5:
            return "stable"
        
        # Simple slope calculation
        n = len(recent)
        x = np.arange(n)
        y = np.array(recent)
        
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / \
                (n * np.sum(x**2) - np.sum(x)**2 + 1e-8)
        
        if slope > 0.5:
            return "worsening"
        elif slope < -0.5:
            return "improving"
        return "stable"
    
    def get_hourly_pattern(self) -> Dict[int, float]:
        """Get congestion pattern by hour (from history)."""
        hourly = {}
        for ts, density in zip(self._timestamps, self._density_history):
            hour = int(time.localtime(ts).tm_hour)
            if hour not in hourly:
                hourly[hour] = []
            hourly[hour].append(density)
        
        return {h: sum(v)/len(v) for h, v in hourly.items()}
    
    def get_stats(self) -> dict:
        """Get congestion statistics."""
        densities = list(self._density_history) if self._density_history else [0]
        speeds = list(self._speed_history) if self._speed_history else [0]
        
        return {
            "current_density": densities[-1] if densities else 0,
            "avg_density": sum(densities) / len(densities),
            "max_density": max(densities),
            "current_avg_speed": speeds[-1] if speeds else 0,
            "min_avg_speed": min(speeds) if speeds else 0,
            "samples": len(densities),
        }
