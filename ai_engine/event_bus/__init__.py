"""
Event Bus - Event-Driven Architecture Core
Transforms the system from direct calls to event-driven.

violation detected → event emitted → backend/alerts/dashboard react independently

This is how real production systems (Uber, Tesla, Google) work.
"""

from .event_manager import EventManager, Event, EventPriority
from .event_types import TrafficEvent

__all__ = ["EventManager", "Event", "EventPriority", "TrafficEvent"]
