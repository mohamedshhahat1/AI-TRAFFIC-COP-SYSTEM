"""
Event Manager - Central Event Bus
Production-grade event-driven architecture for the AI Traffic Cop System.

How it works:
    1. AI detects violation → emits event
    2. Event Bus distributes to ALL registered listeners
    3. Backend, Alerts, Dashboard, Logger ALL react independently
    4. No component knows about the others (fully decoupled)

Architecture:
    ┌─────────────┐    emit()     ┌──────────────┐    notify    ┌──────────────┐
    │  AI Engine  │──────────────▶│  EVENT BUS   │─────────────▶│   Backend    │
    │  (Producer) │               │              │              │  (Consumer)  │
    └─────────────┘               │              │    notify    ├──────────────┤
                                  │              │─────────────▶│Alert Service │
                                  │              │              ├──────────────┤
                                  │              │    notify    │  Dashboard   │
                                  │              │─────────────▶│ (WebSocket)  │
                                  └──────────────┘              └──────────────┘

Features:
    - Sync & Async event handling
    - Event priority levels
    - Wildcard topic matching
    - Event history & replay
    - Dead letter queue (failed events)
    - Middleware/interceptor support
    - Event filtering
    - Rate limiting per topic
    - Metrics & monitoring
"""

import asyncio
import threading
import time
import uuid
from typing import (
    Any, Callable, Dict, List, Optional, Set, Tuple
)
from dataclasses import dataclass, field
from enum import IntEnum
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from loguru import logger


class EventPriority(IntEnum):
    """Event priority levels. Higher = more urgent."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
    EMERGENCY = 4


@dataclass
class Event:
    """
    Represents a single event in the system.
    
    Attributes:
        topic: Event category (e.g., "violation.speed", "accident.risk")
        data: Event payload (any dict)
        priority: Urgency level
        source: Who emitted this event
        event_id: Unique identifier
        timestamp: When it was created
        metadata: Additional context
    """
    topic: str
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    source: str = "system"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Internal state
    _handled: bool = field(default=False, repr=False)
    _handlers_called: int = field(default=0, repr=False)
    
    @property
    def age_seconds(self) -> float:
        """How old is this event."""
        return time.time() - self.timestamp
    
    def to_dict(self) -> Dict:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "topic": self.topic,
            "data": self.data,
            "priority": self.priority.name,
            "source": self.source,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class EventHandler:
    """Registered event handler with metadata."""
    callback: Callable
    topic_pattern: str
    handler_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    is_async: bool = False
    priority_filter: Optional[EventPriority] = None  # Minimum priority
    max_calls: Optional[int] = None  # Auto-unsubscribe after N calls
    _call_count: int = field(default=0, repr=False)


class EventManager:
    """
    Central Event Bus - The nervous system of the AI Traffic Cop.
    
    Usage:
        bus = EventManager()
        
        # Register handlers
        bus.on("violation.speed", handle_speed_violation)
        bus.on("violation.*", log_all_violations)
        bus.on("accident.risk", send_emergency_alert, priority_filter=EventPriority.CRITICAL)
        
        # Emit events
        bus.emit("violation.speed", {
            "track_id": 5,
            "speed": 95.3,
            "limit": 60,
            "severity": "high"
        })
        
        # The event automatically reaches ALL matching handlers
    """
    
    def __init__(self, max_history: int = 5000, enable_dead_letter: bool = True):
        """
        Initialize the Event Manager.
        
        Args:
            max_history: Max events to keep in history
            enable_dead_letter: Keep failed events for retry
        """
        # Handler registry: topic → list of handlers
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        
        # Middleware/interceptors
        self._middleware: List[Callable] = []
        
        # Event history
        self._history: deque = deque(maxlen=max_history)
        
        # Dead letter queue (events that failed to process)
        self._dead_letters: deque = deque(maxlen=1000)
        self._enable_dead_letter = enable_dead_letter
        
        # Metrics
        self._metrics = {
            "total_emitted": 0,
            "total_handled": 0,
            "total_failed": 0,
            "by_topic": defaultdict(int),
            "by_priority": defaultdict(int),
        }
        
        # Rate limiting: topic → (count, window_start)
        self._rate_limits: Dict[str, Tuple[int, int]] = {}
        self._rate_limit_config: Dict[str, int] = {}  # topic → max per second
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Async executor
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("🚌 EventManager initialized (event-driven architecture active)")
    
    # ==================== Registration ====================
    
    def on(
        self,
        topic: str,
        callback: Callable,
        priority_filter: Optional[EventPriority] = None,
        max_calls: Optional[int] = None,
    ) -> str:
        """
        Register an event handler (synchronous).
        
        Args:
            topic: Topic pattern (supports wildcards: "violation.*", "*")
            callback: Function(event: Event) to call
            priority_filter: Only trigger for events >= this priority
            max_calls: Auto-unsubscribe after N invocations
            
        Returns:
            Handler ID (use to unsubscribe)
        """
        handler = EventHandler(
            callback=callback,
            topic_pattern=topic,
            is_async=False,
            priority_filter=priority_filter,
            max_calls=max_calls,
        )
        
        with self._lock:
            self._handlers[topic].append(handler)
        
        logger.debug(f"Handler registered: {topic} → {callback.__name__} [{handler.handler_id}]")
        return handler.handler_id
    
    def on_async(
        self,
        topic: str,
        callback: Callable,
        priority_filter: Optional[EventPriority] = None,
    ) -> str:
        """Register an async event handler."""
        handler = EventHandler(
            callback=callback,
            topic_pattern=topic,
            is_async=True,
            priority_filter=priority_filter,
        )
        
        with self._lock:
            self._handlers[topic].append(handler)
        
        return handler.handler_id
    
    def once(self, topic: str, callback: Callable) -> str:
        """Register handler that fires only once then auto-removes."""
        return self.on(topic, callback, max_calls=1)
    
    def off(self, handler_id: str):
        """Unsubscribe a handler by its ID."""
        with self._lock:
            for topic, handlers in self._handlers.items():
                self._handlers[topic] = [
                    h for h in handlers if h.handler_id != handler_id
                ]
        logger.debug(f"Handler removed: {handler_id}")
    
    def off_topic(self, topic: str):
        """Remove ALL handlers for a topic."""
        with self._lock:
            self._handlers.pop(topic, None)
        logger.debug(f"All handlers removed for: {topic}")
    
    # ==================== Emission ====================
    
    def emit(
        self,
        topic: str,
        data: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        source: str = "ai_engine",
        metadata: Dict = None,
    ) -> Event:
        """
        Emit an event to all matching handlers.
        
        This is the core method. When AI detects something:
            bus.emit("violation.speed", {"track_id": 5, "speed": 95})
        
        All registered handlers for "violation.speed" AND "violation.*" 
        AND "*" will be called.
        
        Args:
            topic: Event topic
            data: Event payload
            priority: Event urgency
            source: Emitter identifier
            metadata: Additional context
            
        Returns:
            The created Event object
        """
        # Rate limiting check
        if not self._check_rate_limit(topic):
            return None
        
        # Create event
        event = Event(
            topic=topic,
            data=data,
            priority=priority,
            source=source,
            metadata=metadata or {},
        )
        
        # Run middleware
        for mw in self._middleware:
            try:
                event = mw(event)
                if event is None:
                    return None  # Middleware cancelled the event
            except Exception as e:
                logger.error(f"Middleware error: {e}")
        
        # Store in history
        self._history.append(event)
        
        # Update metrics
        self._metrics["total_emitted"] += 1
        self._metrics["by_topic"][topic] += 1
        self._metrics["by_priority"][priority.name] += 1
        
        # Find and call matching handlers
        matching_handlers = self._get_matching_handlers(topic, priority)
        
        handlers_to_remove = []
        
        for handler in matching_handlers:
            try:
                if handler.is_async:
                    self._executor.submit(self._call_async_handler, handler, event)
                else:
                    handler.callback(event)
                
                handler._call_count += 1
                event._handlers_called += 1
                self._metrics["total_handled"] += 1
                
                # Check max_calls
                if handler.max_calls and handler._call_count >= handler.max_calls:
                    handlers_to_remove.append(handler.handler_id)
                    
            except Exception as e:
                self._metrics["total_failed"] += 1
                logger.error(f"Handler error on '{topic}': {e}")
                
                if self._enable_dead_letter:
                    self._dead_letters.append({
                        "event": event.to_dict(),
                        "handler": handler.handler_id,
                        "error": str(e),
                        "timestamp": time.time(),
                    })
        
        # Remove expired handlers
        for hid in handlers_to_remove:
            self.off(hid)
        
        event._handled = True
        return event
    
    async def emit_async(
        self,
        topic: str,
        data: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        source: str = "ai_engine",
    ) -> Event:
        """Async version of emit - awaits async handlers."""
        event = Event(topic=topic, data=data, priority=priority, source=source)
        self._history.append(event)
        self._metrics["total_emitted"] += 1
        
        matching = self._get_matching_handlers(topic, priority)
        
        for handler in matching:
            try:
                if handler.is_async:
                    await handler.callback(event)
                else:
                    handler.callback(event)
                handler._call_count += 1
                self._metrics["total_handled"] += 1
            except Exception as e:
                self._metrics["total_failed"] += 1
                logger.error(f"Async handler error: {e}")
        
        return event
    
    def _call_async_handler(self, handler: EventHandler, event: Event):
        """Execute async handler in thread pool."""
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(handler.callback(event))
            loop.close()
        except Exception as e:
            logger.error(f"Async handler execution error: {e}")
    
    # ==================== Pattern Matching ====================
    
    def _get_matching_handlers(
        self, topic: str, priority: EventPriority
    ) -> List[EventHandler]:
        """Find all handlers matching a topic (including wildcards)."""
        matched = []
        
        with self._lock:
            for pattern, handlers in self._handlers.items():
                if self._matches(pattern, topic):
                    for handler in handlers:
                        # Check priority filter
                        if handler.priority_filter and priority < handler.priority_filter:
                            continue
                        matched.append(handler)
        
        # Sort by priority filter (higher priority handlers first)
        matched.sort(
            key=lambda h: h.priority_filter.value if h.priority_filter else 0,
            reverse=True,
        )
        
        return matched
    
    def _matches(self, pattern: str, topic: str) -> bool:
        """Check if a topic matches a pattern (supports wildcards)."""
        if pattern == "*":
            return True
        if pattern == topic:
            return True
        
        # Wildcard matching: "violation.*" matches "violation.speed"
        if "*" in pattern:
            parts_p = pattern.split(".")
            parts_t = topic.split(".")
            
            for pp, pt in zip(parts_p, parts_t):
                if pp == "*":
                    return True
                if pp != pt:
                    return False
            return len(parts_p) <= len(parts_t)
        
        return False
    
    # ==================== Middleware ====================
    
    def use(self, middleware: Callable):
        """
        Add middleware that processes every event before handlers.
        
        Middleware can:
        - Modify events (add metadata, transform data)
        - Filter events (return None to cancel)
        - Log/monitor all events
        
        Args:
            middleware: Function(event: Event) -> Event or None
        """
        self._middleware.append(middleware)
        logger.debug(f"Middleware added: {middleware.__name__}")
    
    # ==================== Rate Limiting ====================
    
    def set_rate_limit(self, topic: str, max_per_second: int):
        """
        Set maximum events per second for a topic.
        Prevents event storms from overwhelming consumers.
        """
        self._rate_limit_config[topic] = max_per_second
    
    def _check_rate_limit(self, topic: str) -> bool:
        """Check if event is within rate limit."""
        if topic not in self._rate_limit_config:
            return True
        
        max_rate = self._rate_limit_config[topic]
        now = int(time.time())
        
        if topic not in self._rate_limits:
            self._rate_limits[topic] = (1, now)
            return True
        
        count, window = self._rate_limits[topic]
        
        if now != window:
            # New second window
            self._rate_limits[topic] = (1, now)
            return True
        
        if count >= max_rate:
            return False
        
        self._rate_limits[topic] = (count + 1, window)
        return True
    
    # ==================== History & Replay ====================
    
    def get_history(self, topic: str = None, limit: int = 50) -> List[Dict]:
        """Get event history, optionally filtered by topic."""
        events = list(self._history)
        
        if topic:
            events = [e for e in events if self._matches(topic, e.topic)]
        
        return [e.to_dict() for e in events[-limit:]]
    
    def replay(self, topic: str = None, since: float = 0):
        """
        Replay historical events to current handlers.
        Useful for new subscribers that missed past events.
        """
        events = list(self._history)
        
        if topic:
            events = [e for e in events if self._matches(topic, e.topic)]
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        count = 0
        for event in events:
            matching = self._get_matching_handlers(event.topic, event.priority)
            for handler in matching:
                try:
                    handler.callback(event)
                    count += 1
                except Exception as e:
                    logger.error(f"Replay error: {e}")
        
        logger.info(f"Replayed {count} events")
    
    # ==================== Dead Letter Queue ====================
    
    def get_dead_letters(self, limit: int = 20) -> List[Dict]:
        """Get failed events from dead letter queue."""
        return list(self._dead_letters)[-limit:]
    
    def retry_dead_letters(self):
        """Retry all failed events."""
        letters = list(self._dead_letters)
        self._dead_letters.clear()
        
        for letter in letters:
            event_data = letter["event"]
            self.emit(
                topic=event_data["topic"],
                data=event_data["data"],
                source="retry",
            )
        
        logger.info(f"Retried {len(letters)} dead letters")
    
    # ==================== Monitoring ====================
    
    def get_metrics(self) -> Dict:
        """Get event bus metrics."""
        return {
            "total_emitted": self._metrics["total_emitted"],
            "total_handled": self._metrics["total_handled"],
            "total_failed": self._metrics["total_failed"],
            "success_rate": round(
                self._metrics["total_handled"] / max(self._metrics["total_emitted"], 1) * 100, 1
            ),
            "registered_handlers": sum(len(h) for h in self._handlers.values()),
            "active_topics": list(self._metrics["by_topic"].keys()),
            "by_priority": dict(self._metrics["by_priority"]),
            "dead_letters": len(self._dead_letters),
            "history_size": len(self._history),
            "middleware_count": len(self._middleware),
        }
    
    def get_handlers_info(self) -> Dict[str, int]:
        """Get handler count per topic."""
        return {topic: len(handlers) for topic, handlers in self._handlers.items()}
    
    # ==================== Lifecycle ====================
    
    def clear(self):
        """Clear all handlers and history."""
        self._handlers.clear()
        self._history.clear()
        self._dead_letters.clear()
        self._middleware.clear()
        logger.info("EventManager cleared")
    
    def shutdown(self):
        """Graceful shutdown."""
        self._executor.shutdown(wait=True)
        logger.info("EventManager shutdown complete")
