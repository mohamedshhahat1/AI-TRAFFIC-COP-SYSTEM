"""
City-Wide Analytics Module
Aggregates data across all cameras for city-level insights.
"""

from typing import Dict, List, Optional
from collections import defaultdict
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("city_analytics")
except ImportError:
    from loguru import logger
import time


class CityAnalytics:
    """
    City-wide traffic analytics engine.
    
    Provides:
    - Traffic flow patterns across the city
    - Peak hour identification
    - Route popularity analysis
    - City-wide violation statistics
    - Environmental impact estimation
    """
    
    def __init__(self):
        self._traffic_data: List[dict] = []
        self._violation_data: List[dict] = []
        self._hourly_patterns: Dict[int, list] = defaultdict(list)
        
        logger.info("CityAnalytics initialized")
    
    def record_traffic_snapshot(self, camera_data: Dict[str, dict]):
        """
        Record a snapshot of city-wide traffic state.
        
        Args:
            camera_data: Dict of camera_id -> {vehicles, speed, congestion}
        """
        snapshot = {
            "timestamp": time.time(),
            "cameras": camera_data,
            "total_vehicles": sum(d.get("vehicles", 0) for d in camera_data.values()),
            "avg_city_speed": self._calc_city_avg_speed(camera_data),
        }
        self._traffic_data.append(snapshot)
        
        # Record hourly pattern
        hour = time.localtime().tm_hour
        self._hourly_patterns[hour].append(snapshot["total_vehicles"])
    
    def get_peak_hours(self) -> List[dict]:
        """Identify peak traffic hours."""
        peaks = []
        for hour, counts in self._hourly_patterns.items():
            if counts:
                avg = sum(counts) / len(counts)
                peaks.append({"hour": hour, "avg_vehicles": round(avg, 1)})
        
        return sorted(peaks, key=lambda x: x["avg_vehicles"], reverse=True)[:5]
    
    def get_busiest_roads(self, camera_locations: Dict[str, str]) -> List[dict]:
        """Identify busiest roads/intersections."""
        road_traffic = defaultdict(list)
        
        for snapshot in self._traffic_data[-100:]:
            for cam_id, data in snapshot.get("cameras", {}).items():
                location = camera_locations.get(cam_id, cam_id)
                road_traffic[location].append(data.get("vehicles", 0))
        
        busiest = []
        for location, counts in road_traffic.items():
            busiest.append({
                "location": location,
                "avg_vehicles": round(sum(counts) / len(counts), 1),
                "max_vehicles": max(counts),
            })
        
        return sorted(busiest, key=lambda x: x["avg_vehicles"], reverse=True)
    
    def get_violation_hotmap(self) -> Dict[str, int]:
        """Get violation frequency by location."""
        hotmap = defaultdict(int)
        for v in self._violation_data:
            hotmap[v.get("location", "unknown")] += 1
        return dict(hotmap)
    
    def estimate_environmental_impact(self, total_vehicles: int, avg_speed: float) -> dict:
        """
        Estimate environmental impact of current traffic.
        Based on simplified emissions model.
        """
        # CO2 emission factor (g/km) - simplified
        if avg_speed < 20:
            emission_factor = 250  # Stop-and-go = high emissions
        elif avg_speed < 50:
            emission_factor = 150
        elif avg_speed < 80:
            emission_factor = 120  # Optimal range
        else:
            emission_factor = 180  # High speed = more emissions
        
        # Noise estimation (dB) - simplified
        if total_vehicles < 10:
            noise_level = 50
        elif total_vehicles < 30:
            noise_level = 65
        elif total_vehicles < 60:
            noise_level = 75
        else:
            noise_level = 85
        
        return {
            "estimated_co2_g_per_km": emission_factor,
            "total_vehicles": total_vehicles,
            "avg_speed_kmh": round(avg_speed, 1),
            "estimated_noise_db": noise_level,
            "air_quality_index": self._estimate_aqi(total_vehicles, avg_speed),
        }
    
    def _estimate_aqi(self, vehicles: int, speed: float) -> str:
        """Simplified Air Quality Index estimation."""
        if vehicles < 10 and speed > 40:
            return "good"
        elif vehicles < 30:
            return "moderate"
        elif vehicles < 60:
            return "unhealthy_sensitive"
        else:
            return "unhealthy"
    
    def _calc_city_avg_speed(self, camera_data: Dict[str, dict]) -> float:
        speeds = [d.get("speed", 0) for d in camera_data.values() if d.get("speed", 0) > 0]
        return sum(speeds) / len(speeds) if speeds else 0.0
    
    def get_dashboard_data(self) -> dict:
        """Get aggregated data for city dashboard."""
        recent = self._traffic_data[-1] if self._traffic_data else {}
        
        result = {
            "current_vehicles": recent.get("total_vehicles", 0),
            "city_avg_speed": recent.get("avg_city_speed", 0),
            "peak_hours": self.get_peak_hours(),
            "total_snapshots": len(self._traffic_data),
        }
        
        # Only compute environmental impact when we have real data
        if recent:
            result["environmental"] = self.estimate_environmental_impact(
                recent.get("total_vehicles", 0),
                recent.get("avg_city_speed", 30),
            )
        else:
            result["environmental"] = {"estimated_co2_g_per_km": 0, "total_vehicles": 0}
        
        return result
