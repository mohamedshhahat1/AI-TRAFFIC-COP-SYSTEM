"""
AI Engine - Core Intelligence Module
The "brain" of the AI Traffic Cop System.

Modules:
    detection/       - YOLOv8 object detection
    tracking/        - DeepSORT multi-object tracking
    speed_estimation/ - Vehicle speed calculation
    violation_detection/ - Traffic violation detection
    prediction/      - Accident & congestion prediction
    smart_city/      - Multi-camera fusion & city analytics
    event_bus/       - Event-driven architecture (pub/sub)
    api_bridge/      - API Gateway & communication layer
    monitoring/      - Logging & metrics (observability)
    pipeline.py      - Main orchestrator
    utils.py         - Utility functions
"""

from .pipeline import AIPipeline
from .event_bus import EventManager, Event, EventPriority, TrafficEvent
from .api_bridge import InferenceService, AIGateway, MessageBroker
from .monitoring import SystemLogger, MetricsCollector, Timer

__all__ = [
    "AIPipeline",
    "EventManager", "Event", "EventPriority", "TrafficEvent",
    "InferenceService", "AIGateway", "MessageBroker",
    "SystemLogger", "MetricsCollector", "Timer",
]
