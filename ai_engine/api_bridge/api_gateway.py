"""
AI Gateway
High-level API facade that unifies all AI services into a single interface.
This is the ONLY class the backend needs to interact with.

Design:
    Backend → AIGateway → InferenceService → Pipeline → Results
                       → MessageBroker → Event subscribers
                       
Benefits:
    - Single entry point for all AI operations
    - Backend doesn't know about pipeline internals
    - Easy to swap AI implementations
    - Can be deployed as a separate microservice (gRPC/REST)
"""

import numpy as np
from typing import Dict, List, Optional, Callable
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("api_gateway")
except ImportError:
    from loguru import logger

from .inference_service import InferenceService
from .message_broker import MessageBroker
from ..event_bus.event_manager import EventManager


class AIGateway:
    """
    Unified AI Gateway - Single interface for all AI operations.
    
    The Backend only interacts with this class.
    All AI complexity is hidden behind this clean API.
    
    Usage:
        gateway = AIGateway(config)
        gateway.start()
        
        # Process a frame
        results = gateway.process_frame(frame)
        
        # Subscribe to events
        gateway.on_violation(send_alert)
        gateway.on_accident_risk(notify_dashboard)
        
        # Get system info
        health = gateway.health()
        metrics = gateway.get_metrics()
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize the AI Gateway.
        
        Args:
            config: Full system configuration
        """
        self.config = config or {}
        
        # Core services
        self.inference = InferenceService(
            config=config,
            max_workers=config.get("max_workers", 2) if config else 2,
        )
        self.broker = MessageBroker()
        
        # Wire up internal event publishing
        self.inference.on_violation(self._publish_violation)
        self.inference.on_accident_risk(self._publish_risk)
        
        self._is_running = False
        logger.info("AIGateway initialized")
    
    def start(self):
        """Start all AI services."""
        self.inference.start()
        self._is_running = True
        logger.info("✅ AIGateway started - all services running")
    
    @property
    def event_bus(self) -> EventManager:
        """
        Access the pipeline's Event Bus directly.
        Provides the full-featured EventManager (priorities, wildcards, replay).
        
        Usage:
            gateway.event_bus.on("violation.*", my_handler)
            gateway.event_bus.on("accident.risk", emergency_handler)
        """
        if self.inference._pipeline:
            return self.inference._pipeline.event_bus
        return None  # Pipeline not started yet
    
    def stop(self):
        """Stop all AI services."""
        self.inference.stop()
        self._is_running = False
        logger.info("🛑 AIGateway stopped")
    
    # ==================== Frame Processing ====================
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single frame through the full AI pipeline.
        This is the primary method called by the backend.
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            Complete results dictionary
        """
        results = self.inference.infer(frame)
        
        # Publish tracking update
        self.broker.publish("tracking.update", {
            "vehicles": results.get("tracking", {}).get("active_vehicles", 0),
            "frame": results.get("frame_number", 0),
        })
        
        return results
    
    def process_frame_async(self, frame: np.ndarray, source: str = "") -> str:
        """
        Submit frame for async processing.
        
        Returns:
            Job ID to retrieve results later
        """
        return self.inference.submit(frame, source)
    
    def get_async_result(self, job_id: str) -> Optional[Dict]:
        """Get result of async processing job."""
        return self.inference.get_result(job_id)
    
    def process_batch(self, frames: List[np.ndarray]) -> List[Dict]:
        """Process multiple frames."""
        return self.inference.infer_batch(frames)
    
    # ==================== Event Subscriptions ====================
    
    def on_violation(self, callback: Callable):
        """Subscribe to violation events. Called when any violation is detected."""
        self.broker.subscribe("violations.new", callback)
    
    def on_critical_violation(self, callback: Callable):
        """Subscribe only to critical/high severity violations."""
        self.broker.subscribe("violations.critical", callback)
    
    def on_accident_risk(self, callback: Callable):
        """Subscribe to accident risk predictions."""
        self.broker.subscribe("accident.risk", callback)
    
    def on_congestion_change(self, callback: Callable):
        """Subscribe to congestion level changes."""
        self.broker.subscribe("congestion.change", callback)
    
    def on_tracking_update(self, callback: Callable):
        """Subscribe to vehicle tracking updates."""
        self.broker.subscribe("tracking.update", callback)
    
    # ==================== Internal Event Publishing ====================
    
    def _publish_violation(self, violation: Dict):
        """Publish violation to message broker."""
        self.broker.publish("violations.new", violation, priority=1)
        
        severity = violation.get("severity", "low")
        if severity in ("high", "critical"):
            self.broker.publish("violations.critical", violation, priority=2)
    
    def _publish_risk(self, risk):
        """Publish accident risk to message broker."""
        risk_data = {
            "level": risk.risk_level if hasattr(risk, 'risk_level') else "unknown",
            "score": risk.risk_score if hasattr(risk, 'risk_score') else 0,
            "vehicles": risk.involved_vehicles if hasattr(risk, 'involved_vehicles') else [],
            "description": risk.description if hasattr(risk, 'description') else "",
        }
        self.broker.publish("accident.risk", risk_data, priority=2)
    
    # ==================== System Info ====================
    
    def health(self) -> Dict:
        """Get gateway health status."""
        return {
            "gateway": "running" if self._is_running else "stopped",
            "inference": self.inference.health(),
            "broker": self.broker.get_stats(),
        }
    
    def get_metrics(self) -> Dict:
        """Get detailed performance metrics."""
        return self.inference.metrics()
    
    def get_event_history(self, topic: str = "violations.new", limit: int = 20) -> List:
        """Get recent events from a topic."""
        return self.broker.get_history(topic, limit)
    
    # ==================== Configuration ====================
    
    def update_config(self, key: str, value):
        """Update a configuration parameter at runtime."""
        self.config[key] = value
        logger.info(f"Config updated: {key} = {value}")
    
    def set_speed_limit(self, limit: float):
        """Update speed limit for violation detection."""
        if self.inference._pipeline:
            self.inference._pipeline.speed_calc.speed_limit = limit
            logger.info(f"Speed limit updated: {limit} km/h")
    
    def set_traffic_light(self, state: str):
        """Update traffic light state (red/green/yellow)."""
        if self.inference._pipeline:
            self.inference._pipeline.violation_engine.set_traffic_light(state)
    
    # ==================== Context Manager ====================
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
