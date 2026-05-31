"""
Multi-Camera Fusion Module
Integrates data from multiple camera feeds for city-wide monitoring.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("multi_camera_fusion")
except ImportError:
    from loguru import logger
import time


@dataclass
class CameraNode:
    """Represents a single camera in the network."""
    camera_id: str
    location: str
    coordinates: Tuple[float, float]  # lat, lng
    status: str = "active"
    vehicle_count: int = 0
    avg_speed: float = 0.0
    violations_count: int = 0
    congestion_level: str = "free"
    last_update: float = field(default_factory=time.time)


@dataclass
class CrossCameraVehicle:
    """Vehicle tracked across multiple cameras."""
    global_id: str
    track_ids: Dict[str, int]  # camera_id -> local_track_id
    vehicle_class: str
    first_seen_camera: str
    last_seen_camera: str
    route: List[str]  # ordered list of camera_ids
    total_violations: int = 0
    avg_speed: float = 0.0


class MultiCameraFusion:
    """
    Fuses data from multiple camera streams for cross-camera tracking.
    
    Features:
    - Cross-camera vehicle re-identification
    - Route reconstruction
    - City-wide vehicle tracking
    - Network-level traffic flow analysis
    """
    
    def __init__(self):
        self.cameras: Dict[str, CameraNode] = {}
        self.global_vehicles: Dict[str, CrossCameraVehicle] = {}
        self._next_global_id = 1
        
        logger.info("MultiCameraFusion initialized")
    
    def register_camera(
        self, camera_id: str, location: str, coordinates: Tuple[float, float]
    ):
        """Register a camera node in the network."""
        self.cameras[camera_id] = CameraNode(
            camera_id=camera_id,
            location=location,
            coordinates=coordinates,
        )
        logger.info(f"Camera registered: {camera_id} @ {location}")
    
    def update_camera(
        self,
        camera_id: str,
        vehicle_count: int,
        avg_speed: float,
        violations: int,
        congestion: str,
    ):
        """Update camera node with latest data."""
        if camera_id not in self.cameras:
            return
        
        cam = self.cameras[camera_id]
        cam.vehicle_count = vehicle_count
        cam.avg_speed = avg_speed
        cam.violations_count = violations
        cam.congestion_level = congestion
        cam.last_update = time.time()
    
    def track_vehicle_across_cameras(
        self,
        camera_id: str,
        local_track_id: int,
        vehicle_class: str,
        appearance_features: Optional[list] = None,
    ) -> str:
        """
        Attempt to match vehicle across cameras.
        
        Returns:
            Global vehicle ID
        """
        # Simple matching based on timing and vehicle class
        # In production, use appearance features (ReID model)
        
        # Check if this local track is already assigned
        for gid, gv in self.global_vehicles.items():
            if camera_id in gv.track_ids and gv.track_ids[camera_id] == local_track_id:
                return gid
        
        # Try to match with recently seen vehicles from adjacent cameras
        matched_id = self._match_vehicle(camera_id, vehicle_class, appearance_features)
        
        if matched_id:
            # Update existing global vehicle
            gv = self.global_vehicles[matched_id]
            gv.track_ids[camera_id] = local_track_id
            gv.last_seen_camera = camera_id
            if camera_id not in gv.route:
                gv.route.append(camera_id)
            return matched_id
        
        # Create new global vehicle
        gid = f"GV-{self._next_global_id:05d}"
        self._next_global_id += 1
        
        self.global_vehicles[gid] = CrossCameraVehicle(
            global_id=gid,
            track_ids={camera_id: local_track_id},
            vehicle_class=vehicle_class,
            first_seen_camera=camera_id,
            last_seen_camera=camera_id,
            route=[camera_id],
        )
        
        return gid
    
    def _match_vehicle(
        self, camera_id: str, vehicle_class: str, features: Optional[list]
    ) -> Optional[str]:
        """
        Match vehicle with recently seen vehicles from other cameras.
        Simplified version - production would use deep ReID features.
        """
        now = time.time()
        
        for gid, gv in self.global_vehicles.items():
            if gv.vehicle_class != vehicle_class:
                continue
            if camera_id in gv.track_ids:
                continue
            
            # Check if seen recently (within 5 minutes)
            last_cam = gv.last_seen_camera
            if last_cam in self.cameras:
                last_update = self.cameras[last_cam].last_update
                if now - last_update < 300:  # 5 minutes
                    return gid
        
        return None
    
    def get_network_status(self) -> dict:
        """Get overall camera network status."""
        active = sum(1 for c in self.cameras.values() if c.status == "active")
        total_vehicles = sum(c.vehicle_count for c in self.cameras.values())
        total_violations = sum(c.violations_count for c in self.cameras.values())
        
        congestion_map = {}
        for cam in self.cameras.values():
            congestion_map[cam.camera_id] = {
                "location": cam.location,
                "congestion": cam.congestion_level,
                "vehicles": cam.vehicle_count,
                "avg_speed": cam.avg_speed,
            }
        
        return {
            "total_cameras": len(self.cameras),
            "active_cameras": active,
            "total_vehicles_tracked": total_vehicles,
            "total_violations": total_violations,
            "global_vehicles": len(self.global_vehicles),
            "congestion_map": congestion_map,
        }
    
    def get_hotspots(self) -> List[dict]:
        """Identify congestion/violation hotspots."""
        hotspots = []
        for cam in self.cameras.values():
            if cam.congestion_level in ("heavy", "gridlock") or cam.violations_count > 5:
                hotspots.append({
                    "camera_id": cam.camera_id,
                    "location": cam.location,
                    "coordinates": cam.coordinates,
                    "congestion": cam.congestion_level,
                    "violations": cam.violations_count,
                    "severity": "high" if cam.congestion_level == "gridlock" else "medium",
                })
        
        return sorted(hotspots, key=lambda x: x["violations"], reverse=True)
