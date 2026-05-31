"""
AI Pipeline - Main orchestrator for the AI Traffic Cop System.
Connects all AI layers into a unified real-time processing pipeline.
"""

import cv2
import numpy as np
from typing import Optional, Dict, List
from loguru import logger
import time

from .detection.yolo_detector import YOLODetector
from .tracking.deep_sort_tracker import DeepSortTracker
from .speed_estimation.speed_calculator import SpeedCalculator
from .violation_detection.violation_engine import ViolationEngine
from .prediction.accident_predictor import AccidentPredictor
from .prediction.congestion_analyzer import CongestionAnalyzer


class AIPipeline:
    """
    Main AI processing pipeline.
    
    Flow:
    Frame → Detection → Tracking → Speed → Violations → Predictions → Output
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize all AI components.
        
        Args:
            config: System configuration dictionary
        """
        cfg = config or {}
        
        logger.info("🧠 Initializing AI Pipeline...")
        
        # Layer 1: Detection
        self.detector = YOLODetector(
            model_name=cfg.get("model", "yolov8n"),
            confidence=cfg.get("confidence", 0.5),
            device=cfg.get("device", "auto"),
        )
        
        # Layer 2: Tracking
        self.tracker = DeepSortTracker(
            max_age=cfg.get("max_age", 30),
            embedder=cfg.get("embedder", "mobilenet"),
        )
        
        # Layer 3: Speed Estimation
        self.speed_calc = SpeedCalculator(
            speed_limit=cfg.get("speed_limit", 60),
            fps=cfg.get("fps", 30),
        )
        
        # Layer 4: Violation Detection
        self.violation_engine = ViolationEngine(config=cfg.get("violations", {}))
        
        # Layer 5: Predictions
        self.accident_predictor = AccidentPredictor()
        self.congestion_analyzer = CongestionAnalyzer()
        
        # Stats
        self.frame_count = 0
        self.start_time = time.time()
        self._last_results = {}
        
        logger.info("✅ AI Pipeline ready")
    
    def process_frame(self, frame: np.ndarray) -> dict:
        """
        Process a single frame through the full pipeline.
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            Dictionary with all pipeline results
        """
        self.frame_count += 1
        t_start = time.time()
        
        # Step 1: Detect objects
        detections = self.detector.detect(frame)
        
        # Step 2: Track vehicles
        tracks = self.tracker.update(detections, frame)
        
        # Step 3: Estimate speeds
        self.speed_calc.update_all(tracks)
        
        # Step 4: Detect violations
        violations = self.violation_engine.process(tracks, frame)
        
        # Step 5: Predict accidents
        accident_risks = self.accident_predictor.analyze(tracks)
        
        # Step 6: Analyze congestion
        congestion = self.congestion_analyzer.analyze(tracks)
        
        # Processing time
        proc_time = (time.time() - t_start) * 1000  # ms
        
        results = {
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
            },
        }
        
        self._last_results = results
        return results
    
    def annotate_frame(self, frame: np.ndarray, results: dict) -> np.ndarray:
        """Draw all pipeline results on frame."""
        annotated = frame.copy()
        
        tracks = results.get("tracks", [])
        violations = results.get("violations", [])
        stats = results.get("stats", {})
        congestion = results.get("congestion")
        
        # Draw tracks with speed
        for track in tracks:
            x1, y1, x2, y2 = track.bbox
            speed = track.current_speed
            
            # Color: green=normal, yellow=above, red=speeding
            if speed > self.speed_calc.speed_limit:
                color = (0, 0, 255)
            elif speed > self.speed_calc.speed_limit * 0.8:
                color = (0, 200, 255)
            else:
                color = (0, 255, 0)
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"#{track.track_id} {speed:.0f}km/h"
            cv2.putText(annotated, label, (x1, y1 - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw trail
            for i in range(1, min(len(track.positions), 20)):
                cv2.line(annotated, track.positions[i-1], track.positions[i], color, 1)
        
        # Draw violation alerts
        y_offset = 30
        for v in violations:
            text = f"⚠ {v.type.value}: Vehicle #{v.track_id}"
            cv2.putText(annotated, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            y_offset += 25
        
        # Draw info bar
        h, w = annotated.shape[:2]
        cv2.rectangle(annotated, (0, h - 40), (w, h), (0, 0, 0), -1)
        info = (
            f"Vehicles: {stats.get('active_tracks', 0)} | "
            f"Violations: {len(self.violation_engine.violations)} | "
            f"Congestion: {congestion.level if congestion else 'N/A'} | "
            f"FPS: {stats.get('fps', 0):.1f}"
        )
        cv2.putText(annotated, info, (10, h - 12),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated
    
    def _calc_fps(self) -> float:
        elapsed = time.time() - self.start_time
        return self.frame_count / elapsed if elapsed > 0 else 0.0
    
    def get_summary(self) -> dict:
        """Get pipeline execution summary."""
        elapsed = time.time() - self.start_time
        return {
            "frames_processed": self.frame_count,
            "elapsed_seconds": round(elapsed, 1),
            "avg_fps": round(self._calc_fps(), 1),
            "total_violations": len(self.violation_engine.violations),
            "tracker_stats": self.tracker.get_stats(),
            "violation_stats": self.violation_engine.get_stats(),
            "congestion_stats": self.congestion_analyzer.get_stats(),
            "prediction_stats": self.accident_predictor.get_stats(),
        }
    
    def reset(self):
        """Reset pipeline state."""
        self.tracker.reset()
        self.frame_count = 0
        self.start_time = time.time()
        logger.info("Pipeline reset")
