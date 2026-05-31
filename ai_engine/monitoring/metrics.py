"""
Metrics Collector
Production-grade performance metrics and system health monitoring.

Features:
- Real-time FPS tracking
- Latency percentiles (p50, p95, p99)
- Component health scoring
- Throughput measurement
- Resource utilization tracking
- Anomaly detection (spike alerts)
- Time-series data export (for Grafana/Prometheus)

Usage:
    from ai_engine.monitoring import MetricsCollector, Timer
    
    metrics = MetricsCollector()
    
    # Track processing time
    with metrics.timer("detection"):
        detections = detector.detect(frame)
    
    # Record values
    metrics.record("vehicles_detected", len(detections))
    metrics.record("frame_processing_ms", 23.4)
    
    # Get stats
    stats = metrics.get_summary()
    # → {"detection": {"avg": 23.1, "p95": 45.2, "count": 1000}, ...}
"""

import time
import threading
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
from loguru import logger


@dataclass
class MetricSample:
    """Single metric measurement."""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


class Timer:
    """
    Standalone timer for measuring execution duration.
    
    Usage:
        timer = Timer()
        timer.start()
        # ... do work ...
        elapsed = timer.stop()
        
        # Or as context manager:
        with Timer() as t:
            # ... do work ...
        print(t.elapsed_ms)
    """
    
    def __init__(self):
        self._start: float = 0.0
        self._end: float = 0.0
        self.elapsed_ms: float = 0.0
    
    def start(self):
        self._start = time.time()
        return self
    
    def stop(self) -> float:
        self._end = time.time()
        self.elapsed_ms = (self._end - self._start) * 1000
        return self.elapsed_ms
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()


class MetricsCollector:
    """
    Central metrics collection and monitoring system.
    
    Collects:
    - Processing latency (per component)
    - Throughput (frames/second, events/second)
    - Detection counts
    - Violation rates
    - System resource usage
    - Error rates
    
    Provides:
    - Real-time dashboards
    - Percentile calculations (p50, p95, p99)
    - Anomaly detection
    - Health scoring
    - Time-series export
    """
    
    def __init__(self, window_size: int = 1000, health_check_interval: float = 30.0):
        """
        Initialize metrics collector.
        
        Args:
            window_size: Number of samples to keep per metric
            health_check_interval: Seconds between health evaluations
        """
        self._window_size = window_size
        self._health_interval = health_check_interval
        
        # Metric storage: name → deque of values
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self._timestamps: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        
        # Counters (monotonically increasing)
        self._counters: Dict[str, int] = defaultdict(int)
        
        # Gauges (current values)
        self._gauges: Dict[str, float] = {}
        
        # Timers
        self._active_timers: Dict[str, float] = {}
        
        # Health thresholds
        self._thresholds: Dict[str, Dict[str, float]] = {
            "frame_processing_ms": {"warning": 100, "critical": 200},
            "detection_ms": {"warning": 50, "critical": 100},
            "tracking_ms": {"warning": 30, "critical": 60},
            "error_rate": {"warning": 0.05, "critical": 0.1},
        }
        
        # State
        self._start_time = time.time()
        self._lock = threading.Lock()
        
        # Anomaly detection
        self._anomaly_callbacks = []
        
        logger.info("MetricsCollector initialized")
    
    # ==================== Recording ====================
    
    def record(self, name: str, value: float, **tags):
        """
        Record a metric value.
        
        Args:
            name: Metric name (e.g., "detection_ms", "vehicles_count")
            value: Numeric value
            **tags: Optional tags for filtering
        """
        with self._lock:
            self._metrics[name].append(value)
            self._timestamps[name].append(time.time())
        
        # Check for anomalies
        self._check_anomaly(name, value)
    
    def increment(self, name: str, amount: int = 1):
        """Increment a counter."""
        with self._lock:
            self._counters[name] += amount
    
    def gauge(self, name: str, value: float):
        """Set a gauge value (point-in-time measurement)."""
        self._gauges[name] = value
    
    def timer(self, name: str):
        """
        Context manager timer that auto-records duration.
        
        Usage:
            with metrics.timer("detection"):
                result = detect(frame)
        """
        return _MetricTimer(self, name)
    
    def start_timer(self, name: str):
        """Start a named timer manually."""
        self._active_timers[name] = time.time()
    
    def stop_timer(self, name: str) -> float:
        """Stop a named timer and record the duration."""
        start = self._active_timers.pop(name, None)
        if start is None:
            return 0.0
        elapsed_ms = (time.time() - start) * 1000
        self.record(f"{name}_ms", elapsed_ms)
        return elapsed_ms
    
    # ==================== Querying ====================
    
    def get(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a metric.
        
        Returns:
            Dict with avg, min, max, p50, p95, p99, count, latest
        """
        values = list(self._metrics.get(name, []))
        if not values:
            return {"count": 0}
        
        arr = np.array(values)
        return {
            "count": len(arr),
            "latest": float(arr[-1]),
            "avg": float(np.mean(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "std": float(np.std(arr)),
            "p50": float(np.percentile(arr, 50)),
            "p95": float(np.percentile(arr, 95)),
            "p99": float(np.percentile(arr, 99)),
        }
    
    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self._counters.get(name, 0)
    
    def get_gauge(self, name: str) -> float:
        """Get gauge value."""
        return self._gauges.get(name, 0.0)
    
    def get_rate(self, name: str, window_seconds: float = 60.0) -> float:
        """
        Get rate of events per second over a time window.
        
        Args:
            name: Metric name
            window_seconds: Time window to calculate rate over
        """
        timestamps = list(self._timestamps.get(name, []))
        if not timestamps:
            return 0.0
        
        now = time.time()
        cutoff = now - window_seconds
        recent = [t for t in timestamps if t > cutoff]
        
        return len(recent) / window_seconds
    
    # ==================== Health ====================
    
    def get_health(self) -> Dict[str, Any]:
        """
        Get system health assessment.
        
        Returns:
            Health report with status per component and overall score.
        """
        health = {
            "status": "healthy",
            "score": 100.0,
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "components": {},
            "alerts": [],
        }
        
        issues = 0
        
        for metric_name, thresholds in self._thresholds.items():
            stats = self.get(metric_name)
            if stats.get("count", 0) == 0:
                continue
            
            avg = stats.get("avg", 0)
            p95 = stats.get("p95", 0)
            status = "healthy"
            
            if p95 > thresholds.get("critical", float("inf")):
                status = "critical"
                issues += 2
                health["alerts"].append(f"{metric_name} p95={p95:.1f} exceeds critical threshold")
            elif p95 > thresholds.get("warning", float("inf")):
                status = "degraded"
                issues += 1
                health["alerts"].append(f"{metric_name} p95={p95:.1f} exceeds warning threshold")
            
            health["components"][metric_name] = {
                "status": status,
                "avg": round(avg, 2),
                "p95": round(p95, 2),
            }
        
        # Calculate score
        health["score"] = max(0, 100 - issues * 15)
        if health["score"] < 50:
            health["status"] = "critical"
        elif health["score"] < 80:
            health["status"] = "degraded"
        
        return health
    
    def set_threshold(self, metric_name: str, warning: float, critical: float):
        """Set health thresholds for a metric."""
        self._thresholds[metric_name] = {"warning": warning, "critical": critical}
    
    # ==================== Summary ====================
    
    def get_summary(self) -> Dict[str, Any]:
        """Get full metrics summary."""
        summary = {
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "metrics": {},
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "health": self.get_health(),
        }
        
        for name in self._metrics:
            summary["metrics"][name] = self.get(name)
        
        return summary
    
    def get_fps(self) -> float:
        """Get current processing FPS."""
        return self.get_rate("frame_processed", window_seconds=5.0)
    
    # ==================== Anomaly Detection ====================
    
    def on_anomaly(self, callback):
        """Register callback for anomaly detection."""
        self._anomaly_callbacks.append(callback)
    
    def _check_anomaly(self, name: str, value: float):
        """Check if a value is anomalous (> 3 std deviations from mean)."""
        values = list(self._metrics.get(name, []))
        if len(values) < 30:
            return
        
        arr = np.array(values[:-1])  # Exclude current value
        mean = np.mean(arr)
        std = np.std(arr)
        
        if std > 0 and abs(value - mean) > 3 * std:
            anomaly = {
                "metric": name,
                "value": value,
                "mean": round(float(mean), 2),
                "std": round(float(std), 2),
                "deviation": round(abs(value - mean) / std, 1),
                "timestamp": time.time(),
            }
            
            for cb in self._anomaly_callbacks:
                try:
                    cb(anomaly)
                except Exception:
                    pass
    
    # ==================== Export ====================
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        for name, values in self._metrics.items():
            if not values:
                continue
            safe_name = name.replace(".", "_").replace("-", "_")
            arr = list(values)
            lines.append(f"# TYPE traffic_cop_{safe_name} gauge")
            lines.append(f"traffic_cop_{safe_name}_avg {np.mean(arr):.4f}")
            lines.append(f"traffic_cop_{safe_name}_p95 {np.percentile(arr, 95):.4f}")
            lines.append(f"traffic_cop_{safe_name}_count {len(arr)}")
        
        for name, count in self._counters.items():
            safe_name = name.replace(".", "_").replace("-", "_")
            lines.append(f"# TYPE traffic_cop_{safe_name}_total counter")
            lines.append(f"traffic_cop_{safe_name}_total {count}")
        
        return "\n".join(lines)
    
    def export_json(self) -> dict:
        """Export all metrics as JSON (for dashboard)."""
        return self.get_summary()
    
    # ==================== Reset ====================
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._timestamps.clear()
            self._counters.clear()
            self._gauges.clear()
            self._start_time = time.time()


class _MetricTimer:
    """Context manager timer for MetricsCollector."""
    
    def __init__(self, collector: MetricsCollector, name: str):
        self._collector = collector
        self._name = name
        self._start = 0.0
        self.elapsed_ms = 0.0
    
    def __enter__(self):
        self._start = time.time()
        return self
    
    def __exit__(self, *args):
        self.elapsed_ms = (time.time() - self._start) * 1000
        self._collector.record(f"{self._name}_ms", self.elapsed_ms)
