"""
Traffic Event Types
Pre-defined event types for the AI Traffic Cop System.
Provides typed, documented events for consistent usage across the system.

Usage:
    from ai_engine.event_bus import TrafficEvent, EventManager
    
    bus = EventManager()
    
    # Emit typed events
    TrafficEvent.speed_violation(bus, track_id=5, speed=95, limit=60)
    TrafficEvent.red_light(bus, track_id=8, speed=45)
    TrafficEvent.accident_risk(bus, vehicles=[3, 7], ttc=1.2, level="critical")
    TrafficEvent.congestion_change(bus, level="heavy", density=45.2)
"""

from typing import Dict, List, Any
from .event_manager import EventManager, EventPriority


class TrafficEvent:
    """
    Factory class for creating standardized traffic events.
    Ensures consistent event structure across the system.
    
    Event Topics:
    ─────────────────────────────────────────────────
    violation.speed          Speed limit exceeded
    violation.red_light      Red light running
    violation.lane           Illegal lane change
    violation.parking        Illegal parking
    violation.any            Any violation (catch-all)
    
    accident.risk            Collision risk detected
    accident.imminent        Imminent collision (< 1.5s TTC)
    
    tracking.new_vehicle     New vehicle entered frame
    tracking.vehicle_lost    Vehicle left frame
    tracking.update          Periodic tracking update
    
    congestion.change        Congestion level changed
    congestion.gridlock      Gridlock detected
    
    system.started           System started
    system.stopped           System stopped
    system.error             System error occurred
    system.health            Periodic health check
    
    camera.connected         Camera came online
    camera.disconnected      Camera went offline
    ─────────────────────────────────────────────────
    """
    
    # ==================== Violation Events ====================
    
    @staticmethod
    def speed_violation(
        bus: EventManager,
        track_id: int,
        speed: float,
        limit: float,
        vehicle_class: str = "car",
        severity: str = "medium",
        location: tuple = (0, 0),
        snapshot_path: str = None,
    ):
        """Emit speed violation event."""
        excess = speed - limit
        
        # Auto-determine priority from severity
        priority_map = {
            "low": EventPriority.NORMAL,
            "medium": EventPriority.HIGH,
            "high": EventPriority.CRITICAL,
            "critical": EventPriority.EMERGENCY,
        }
        
        bus.emit(
            topic="violation.speed",
            data={
                "track_id": track_id,
                "vehicle_class": vehicle_class,
                "speed": round(speed, 1),
                "speed_limit": limit,
                "excess": round(excess, 1),
                "severity": severity,
                "location": location,
                "snapshot_path": snapshot_path,
            },
            priority=priority_map.get(severity, EventPriority.NORMAL),
            source="violation_engine",
        )
        
        # Also emit generic violation event
        bus.emit("violation.any", {
            "type": "speed", "track_id": track_id, "severity": severity,
        }, priority=EventPriority.NORMAL)
    
    @staticmethod
    def red_light(
        bus: EventManager,
        track_id: int,
        speed: float,
        vehicle_class: str = "car",
        location: tuple = (0, 0),
    ):
        """Emit red light violation event (always HIGH+ priority)."""
        severity = "critical" if speed > 50 else "high"
        
        bus.emit(
            topic="violation.red_light",
            data={
                "track_id": track_id,
                "vehicle_class": vehicle_class,
                "speed": round(speed, 1),
                "severity": severity,
                "location": location,
            },
            priority=EventPriority.CRITICAL,
            source="violation_engine",
        )
        
        bus.emit("violation.any", {
            "type": "red_light", "track_id": track_id, "severity": severity,
        }, priority=EventPriority.HIGH)
    
    @staticmethod
    def lane_violation(
        bus: EventManager,
        track_id: int,
        vehicle_class: str = "car",
        speed: float = 0,
    ):
        """Emit lane violation event."""
        bus.emit(
            topic="violation.lane",
            data={
                "track_id": track_id,
                "vehicle_class": vehicle_class,
                "speed": round(speed, 1),
                "severity": "high" if speed > 80 else "medium",
            },
            priority=EventPriority.HIGH,
            source="violation_engine",
        )
    
    @staticmethod
    def parking_violation(
        bus: EventManager,
        track_id: int,
        duration: float,
        vehicle_class: str = "car",
    ):
        """Emit parking violation event."""
        bus.emit(
            topic="violation.parking",
            data={
                "track_id": track_id,
                "vehicle_class": vehicle_class,
                "duration_seconds": round(duration, 0),
                "severity": "low",
            },
            priority=EventPriority.LOW,
            source="violation_engine",
        )
    
    # ==================== Accident Events ====================
    
    @staticmethod
    def accident_risk(
        bus: EventManager,
        vehicles: List[int],
        ttc: float,
        level: str = "medium",
        risk_score: float = 0.5,
        collision_point: tuple = None,
    ):
        """Emit accident risk prediction event."""
        priority = EventPriority.EMERGENCY if level == "imminent" else EventPriority.CRITICAL
        
        bus.emit(
            topic="accident.risk",
            data={
                "involved_vehicles": vehicles,
                "time_to_collision": round(ttc, 2),
                "risk_level": level,
                "risk_score": round(risk_score, 2),
                "collision_point": collision_point,
            },
            priority=priority,
            source="accident_predictor",
        )
        
        if level == "imminent":
            bus.emit(
                topic="accident.imminent",
                data={"vehicles": vehicles, "ttc": ttc},
                priority=EventPriority.EMERGENCY,
                source="accident_predictor",
            )
    
    # ==================== Tracking Events ====================
    
    @staticmethod
    def new_vehicle(
        bus: EventManager,
        track_id: int,
        vehicle_class: str,
        location: tuple = (0, 0),
    ):
        """Emit new vehicle detected event."""
        bus.emit(
            topic="tracking.new_vehicle",
            data={
                "track_id": track_id,
                "vehicle_class": vehicle_class,
                "location": location,
            },
            priority=EventPriority.LOW,
            source="tracker",
        )
    
    @staticmethod
    def vehicle_lost(bus: EventManager, track_id: int, duration: float):
        """Emit vehicle left frame event."""
        bus.emit(
            topic="tracking.vehicle_lost",
            data={"track_id": track_id, "tracked_duration": round(duration, 1)},
            priority=EventPriority.LOW,
            source="tracker",
        )
    
    @staticmethod
    def tracking_update(
        bus: EventManager,
        active_count: int,
        speeds: Dict[int, float] = None,
    ):
        """Emit periodic tracking summary."""
        bus.emit(
            topic="tracking.update",
            data={
                "active_vehicles": active_count,
                "vehicle_speeds": speeds or {},
            },
            priority=EventPriority.LOW,
            source="tracker",
        )
    
    # ==================== Congestion Events ====================
    
    @staticmethod
    def congestion_change(
        bus: EventManager,
        level: str,
        density: float,
        avg_speed: float = 0,
        prediction: str = "stable",
    ):
        """Emit congestion level change event."""
        priority = EventPriority.HIGH if level in ("heavy", "gridlock") else EventPriority.NORMAL
        
        bus.emit(
            topic="congestion.change",
            data={
                "level": level,
                "density": round(density, 1),
                "avg_speed": round(avg_speed, 1),
                "prediction": prediction,
            },
            priority=priority,
            source="congestion_analyzer",
        )
        
        if level == "gridlock":
            bus.emit(
                topic="congestion.gridlock",
                data={"density": density, "avg_speed": avg_speed},
                priority=EventPriority.CRITICAL,
                source="congestion_analyzer",
            )
    
    # ==================== System Events ====================
    
    @staticmethod
    def system_started(bus: EventManager):
        """Emit system started event."""
        bus.emit("system.started", {"message": "AI Traffic Cop System started"}, source="system")
    
    @staticmethod
    def system_stopped(bus: EventManager):
        """Emit system stopped event."""
        bus.emit("system.stopped", {"message": "System stopped"}, source="system")
    
    @staticmethod
    def system_error(bus: EventManager, error: str, component: str = "unknown"):
        """Emit system error event."""
        bus.emit(
            topic="system.error",
            data={"error": error, "component": component},
            priority=EventPriority.CRITICAL,
            source="system",
        )
    
    @staticmethod
    def camera_connected(bus: EventManager, camera_id: str, location: str = ""):
        """Emit camera online event."""
        bus.emit("camera.connected", {"camera_id": camera_id, "location": location}, source="camera")
    
    @staticmethod
    def camera_disconnected(bus: EventManager, camera_id: str):
        """Emit camera offline event."""
        bus.emit(
            "camera.disconnected",
            {"camera_id": camera_id},
            priority=EventPriority.HIGH,
            source="camera",
        )
