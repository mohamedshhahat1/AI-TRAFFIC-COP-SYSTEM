"""
Message Broker
Handles asynchronous communication between AI Engine and Backend.
Supports pub/sub pattern for real-time event distribution.

Enables:
- Backend subscribes to violation events
- Alert system subscribes to critical events
- Dashboard receives live tracking updates
- Multiple consumers without coupling
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger
import time
import json


@dataclass
class Message:
    """A message in the broker system."""
    topic: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    source: str = "ai_engine"
    priority: int = 0  # 0=normal, 1=high, 2=critical


class MessageBroker:
    """
    In-process message broker for event-driven communication.
    
    Topics:
    - violations.new         → New violation detected
    - violations.critical    → Critical severity violations
    - tracking.update        → Vehicle tracking updates
    - congestion.change      → Congestion level changed
    - accident.risk          → Accident risk detected
    - system.health          → System health updates
    
    Usage:
        broker = MessageBroker()
        
        # Subscribe
        broker.subscribe("violations.new", handle_violation)
        broker.subscribe("accident.risk", handle_risk)
        
        # Publish
        broker.publish("violations.new", {"track_id": 5, "type": "speed"})
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize message broker.
        
        Args:
            max_history: Maximum messages to keep in history per topic
        """
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._async_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._history: Dict[str, List[Message]] = defaultdict(list)
        self._max_history = max_history
        self._message_count = 0
        
        logger.info("MessageBroker initialized")
    
    def subscribe(self, topic: str, callback: Callable):
        """
        Subscribe to a topic with a synchronous callback.
        
        Args:
            topic: Topic pattern (supports wildcards: "violations.*")
            callback: Function(payload: dict) called when message arrives
        """
        self._subscribers[topic].append(callback)
        logger.debug(f"Subscriber added: {topic} → {callback.__name__}")
    
    def subscribe_async(self, topic: str, callback: Callable):
        """
        Subscribe with an async callback.
        
        Args:
            topic: Topic to subscribe to
            callback: Async function(payload: dict)
        """
        self._async_subscribers[topic].append(callback)
        logger.debug(f"Async subscriber added: {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable):
        """Remove a subscriber from a topic."""
        if callback in self._subscribers.get(topic, []):
            self._subscribers[topic].remove(callback)
        if callback in self._async_subscribers.get(topic, []):
            self._async_subscribers[topic].remove(callback)
    
    def publish(self, topic: str, payload: Dict[str, Any], priority: int = 0):
        """
        Publish a message to a topic.
        
        Args:
            topic: Target topic
            payload: Message data
            priority: 0=normal, 1=high, 2=critical
        """
        message = Message(topic=topic, payload=payload, priority=priority)
        self._message_count += 1
        
        # Store in history
        self._history[topic].append(message)
        if len(self._history[topic]) > self._max_history:
            self._history[topic] = self._history[topic][-self._max_history:]
        
        # Notify sync subscribers
        self._notify_sync(topic, payload)
        
        # Notify wildcard subscribers
        parts = topic.split(".")
        if len(parts) > 1:
            wildcard = f"{parts[0]}.*"
            self._notify_sync(wildcard, payload)
    
    async def publish_async(self, topic: str, payload: Dict[str, Any], priority: int = 0):
        """Publish and notify async subscribers."""
        self.publish(topic, payload, priority)
        await self._notify_async(topic, payload)
    
    def _notify_sync(self, topic: str, payload: Dict):
        """Notify synchronous subscribers."""
        for callback in self._subscribers.get(topic, []):
            try:
                callback(payload)
            except Exception as e:
                logger.error(f"Subscriber error on '{topic}': {e}")
    
    async def _notify_async(self, topic: str, payload: Dict):
        """Notify async subscribers."""
        for callback in self._async_subscribers.get(topic, []):
            try:
                await callback(payload)
            except Exception as e:
                logger.error(f"Async subscriber error on '{topic}': {e}")
    
    def get_history(self, topic: str, limit: int = 50) -> List[Dict]:
        """Get message history for a topic."""
        messages = self._history.get(topic, [])[-limit:]
        return [
            {
                "topic": m.topic,
                "payload": m.payload,
                "timestamp": m.timestamp,
                "priority": m.priority,
            }
            for m in messages
        ]
    
    def get_topics(self) -> List[str]:
        """List all active topics."""
        return list(set(
            list(self._subscribers.keys()) +
            list(self._async_subscribers.keys()) +
            list(self._history.keys())
        ))
    
    def get_stats(self) -> Dict:
        """Get broker statistics."""
        return {
            "total_messages": self._message_count,
            "active_topics": len(self.get_topics()),
            "total_subscribers": sum(len(v) for v in self._subscribers.values()),
            "total_async_subscribers": sum(len(v) for v in self._async_subscribers.values()),
            "history_size": sum(len(v) for v in self._history.values()),
        }
    
    def clear_history(self):
        """Clear all message history."""
        self._history.clear()
        logger.info("Message history cleared")
