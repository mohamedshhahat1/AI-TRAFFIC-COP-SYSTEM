"""
AI Pipeline - Main orchestrator for the AI Traffic Cop System.
Connects all AI layers into a unified real-time processing pipeline.
Fully event-driven with comprehensive monitoring & metrics.

Flow:
Frame → Detection → Tracking → Speed → Violations → Predictions → Events → Output
         (timed)    (timed)   (timed)    (timed)       (timed)      (logged)
"""

import cv2
import numpy as np
from typing import Optional, Dict, List
import time

from .detection.yolo_detector import YOLODetector
from .tracking.deep_sort_tracker import DeepSortTracker
from .speed_estimation.speed_calculator import SpeedCalculator
from .violation_detection.violation_engine import ViolationEngine
from .prediction.accident_predictor import AccidentPredictor
from .prediction.congestion_analyzer import CongestionAnalyzer
from .event_bus.event_manager import EventManager, EventPriority
from .event_bus.event_types import TrafficEvent
from .monitoring.logger import SystemLogger
from .monitoring.metrics import MetricsCollector


class AIPipeline:
    """
    Main AI processing pipeline with full observability.
    
    Every layer is:
    - Timed (latency tracked via MetricsCollector)
    - Logged (structured logs via SystemLogger)
    - Event-emitting (violations/risks → Event Bus)
    """
    
    def __init__(self, config: dict = None):
        cfg = config or {}
        
        # Monitoring (initialized FIRST)
        self.log = SystemLogger("pipeline")
        self.metrics = MetricsCollector()
        
        self.log.info("Initializing AI Pipeline...")
        
        # Event Bus
        self.event_bus = EventManager()
        
        # Layer 1: Detection
        self.log.info("Loading detection model...")
        self.detector = YOLODetector(
            model_name=cfg.get("detection", {}).get("model", cfg.get("model", "yolov8n")),
            confidence=cfg.get("detection", {}).get("confidence", cfg.get("confidence", 0.35)),
            device=cfg.get("detection", {}).get("device", cfg.get("device", "auto")),
        )
        
        # Layer 2: Tracking
        self.tracker = DeepSortTracker(
            max_age=cfg.get("tracking", {}).get("max_age", cfg.get("max_age", 70)),
            embedder=cfg.get("tracking", {}).get("embedder", cfg.get("embedder", "mobilenet")),
        )
        
        # Layer 3: Speed
        self.speed_calc = SpeedCalculator(
            speed_limit=cfg.get("speed", {}).get("limit", cfg.get("speed_limit", 60)),
            fps=cfg.get("camera", {}).get("fps", cfg.get("fps", 30)),
        )
        
        # Layer 4: Violations
        self.violation_engine = ViolationEngine(config=cfg.get("violations", {}))
        
        # Layer 5: Predictions
        self.accident_predictor = AccidentPredictor()
        self.congestion_analyzer = CongestionAnalyzer()
        
        # State
        self.frame_count = 0
        self.start_time = time.time()
        self._prev_congestion_level = "free"
        
        # Emit system started
        TrafficEvent.system_started(self.event_bus)
        self.log.info("AI Pipeline ready", components=6, event_driven=True)
    
    def process_frame(self, frame: np.ndarray) -> dict:
        """
        Process a single frame through the full pipeline.
        Every layer is timed and logged.
        """
        self.frame_count += 1
        self.metrics.increment("frames_total")
        t_start = time.time()
        
        # === DETECTION (timed) ===
        with self.metrics.timer("detection"):
            detections = self.detector.detect(frame)
        self.metrics.record("detections_count", len(detections))
        
        # === TRACKING (timed) ===
        with self.metrics.timer("tracking"):
            prev_ids = set(t.track_id for t in self.tracker.get_active())
            tracks = self.tracker.update(detections, frame)
            curr_ids = set(t.track_id for t in tracks)
        self.metrics.record("active_tracks", len(tracks))
        self.metrics.gauge("vehicles_on_screen", len(tracks))
        
        # Emit new/lost vehicle events
        for tid in curr_ids - prev_ids:
            track = next((t for t in tracks if t.track_id == tid), None)
            if track:
                TrafficEvent.new_vehicle(self.event_bus, track.track_id, track.class_name, track.center)
                self.metrics.increment("vehicles_entered")
        
        for tid in prev_ids - curr_ids:
            TrafficEvent.vehicle_lost(self.event_bus, tid, 0)
            self.metrics.increment("vehicles_exited")
        
        # === SPEED ESTIMATION (timed) ===
        with self.metrics.timer("speed_estimation"):
            self.speed_calc.update_all(tracks)
        
        # === VIOLATION DETECTION (timed) ===
        with self.metrics.timer("violation_detection"):
            violations = self.violation_engine.process(tracks, frame)
        
        if violations:
            self.metrics.increment("violations_total", len(violations))
            for v in violations:
                self.metrics.increment(f"violation_{v.type.value}")
                self._emit_violation_event(v)
                self.log.warning(
                    f"Violation detected: {v.type.value}",
                    track_id=v.track_id, severity=v.severity, speed=v.speed,
                )
        
        # === PREDICTION (timed) ===
        with self.metrics.timer("prediction"):
            accident_risks = self.accident_predictor.analyze(tracks)
            congestion = self.congestion_analyzer.analyze(tracks)
        
        # Emit accident risks
        for risk in accident_risks:
            self.metrics.increment("accident_risks_total")
            TrafficEvent.accident_risk(
                self.event_bus,
                vehicles=risk.involved_vehicles,
                ttc=risk.time_to_collision,
                level=risk.risk_level,
                risk_score=risk.risk_score,
                collision_point=risk.predicted_collision_point,
            )
            self.log.error(
                f"Accident risk: {risk.risk_level}",
                vehicles=risk.involved_vehicles, ttc=risk.time_to_collision,
            )
        
        # Emit congestion change
        if congestion.level != self._prev_congestion_level:
            TrafficEvent.congestion_change(
                self.event_bus,
                level=congestion.level,
                density=congestion.density,
                avg_speed=congestion.avg_speed,
                prediction=congestion.prediction,
            )
            self.log.info(
                f"Congestion changed: {self._prev_congestion_level} → {congestion.level}",
                density=congestion.density,
            )
            self._prev_congestion_level = congestion.level
        
        # Periodic tracking update
        if self.frame_count % 30 == 0:
            TrafficEvent.tracking_update(
                self.event_bus,
                active_count=len(tracks),
                speeds={t.track_id: round(t.current_speed, 1) for t in tracks},
            )
        
        # === TOTAL FRAME TIME ===
        proc_time = (time.time() - t_start) * 1000
        self.metrics.record("frame_processing_ms", proc_time)
        self.metrics.record("frame_processed", 1)
        
        # Log every 100 frames
        if self.frame_count % 100 == 0:
            health = self.metrics.get_health()
            self.log.info(
                f"Frame {self.frame_count}",
                fps=round(self._calc_fps(), 1),
                vehicles=len(tracks),
                violations=len(self.violation_engine.violations),
                health_score=health["score"],
                proc_ms=round(proc_time, 1),
            )
        
        return {
            "frame_number": self.frame_count,
            "detections": detections,
            "tracks": tracks,
            "violations": violations,
            "accident_risks": accident_risks,
            "congestion": congestion,
            "stats": {
                "detected_objects": len(detections),
                "active_tracks": len(tracks),
                "new_violations": len(violations),
                "accident_risks": len(accident_risks),
                "congestion_level": congestion.level,
                "processing_time_ms": round(proc_time, 1),
                "fps": self._calc_fps(),
                "events_emitted": self.event_bus.get_metrics()["total_emitted"],
                "health_score": self.metrics.get_health()["score"],
            },
        }
    
    def _emit_violation_event(self, v):
        """Emit typed event for a violation."""
        if v.type.value == "speed_violation":
            TrafficEvent.speed_violation(
                self.event_bus, track_id=v.track_id, speed=v.speed,
                limit=v.speed_limit, vehicle_class=v.vehicle_class,
                severity=v.severity, location=v.location, snapshot_path=v.snapshot_path,
            )
        elif v.type.value == "red_light_violation":
            TrafficEvent.red_light(
                self.event_bus, track_id=v.track_id, speed=v.speed,
                vehicle_class=v.vehicle_class, location=v.location,
            )
        elif v.type.value == "lane_violation":
            TrafficEvent.lane_violation(
                self.event_bus, track_id=v.track_id,
                vehicle_class=v.vehicle_class, speed=v.speed,
            )
        elif v.type.value == "parking_violation":
            TrafficEvent.parking_violation(
                self.event_bus, track_id=v.track_id,
                duration=0, vehicle_class=v.vehicle_class,
            )
    
    def annotate_frame(self, frame: np.ndarray, results: dict) -> np.ndarray:
        """Draw all pipeline results on frame."""
        annotated = frame.copy()
        tracks = results.get("tracks", [])
        violations = results.get("violations", [])
        stats = results.get("stats", {})
        congestion = results.get("congestion")
        
        for track in tracks:
            x1, y1, x2, y2 = track.bbox
            speed = track.current_speed
            color = (0, 0, 255) if speed > self.speed_calc.speed_limit else (0, 255, 0)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(annotated, f"#{track.track_id} {speed:.0f}km/h", (x1, y1 - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            for i in range(1, min(len(track.positions), 20)):
                cv2.line(annotated, track.positions[i-1], track.positions[i], color, 1)
        
        y_off = 30
        for v in violations:
            cv2.putText(annotated, f"!! {v.type.value}: #{v.track_id}", (10, y_off),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            y_off += 25
        
        h, w = annotated.shape[:2]
        cv2.rectangle(annotated, (0, h - 40), (w, h), (0, 0, 0), -1)
        info = (
            f"FPS: {stats.get('fps', 0):.1f} | "
            f"Vehicles: {stats.get('active_tracks', 0)} | "
            f"Violations: {len(self.violation_engine.violations)} | "
            f"Health: {stats.get('health_score', 100)}% | "
            f"Congestion: {congestion.level if congestion else 'N/A'}"
        )
        cv2.putText(annotated, info, (10, h - 12),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        return annotated
    
    def _calc_fps(self) -> float:
        elapsed = time.time() - self.start_time
        return self.frame_count / elapsed if elapsed > 0 else 0.0
    
    def get_summary(self) -> dict:
        return {
            "frames_processed": self.frame_count,
            "elapsed_seconds": round(time.time() - self.start_time, 1),
            "avg_fps": round(self._calc_fps(), 1),
            "total_violations": len(self.violation_engine.violations),
            "tracker_stats": self.tracker.get_stats(),
            "violation_stats": self.violation_engine.get_stats(),
            "congestion_stats": self.congestion_analyzer.get_stats(),
            "prediction_stats": self.accident_predictor.get_stats(),
            "event_bus_metrics": self.event_bus.get_metrics(),
            "monitoring": self.metrics.get_summary(),
            "health": self.metrics.get_health(),
            "log_stats": SystemLogger.get_stats(),
        }
    
    def reset(self):
        self.tracker.reset()
        self.event_bus.clear()
        self.metrics.reset()
        self.frame_count = 0
        self.start_time = time.time()
        self.log.info("Pipeline reset")
    
    def shutdown(self):
        TrafficEvent.system_stopped(self.event_bus)
        self.event_bus.shutdown()
        self.log.info("Pipeline shutdown", total_frames=self.frame_count)
