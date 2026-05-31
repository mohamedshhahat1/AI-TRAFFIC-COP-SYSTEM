"""
AI Traffic Cop System - Main Entry Point
Smart Traffic Enforcement & Analytics System

Usage:
    python main.py                              # Run with default config
    python main.py --source video.mp4           # Process video file
    python main.py --source rtsp://camera/stream # Connect to RTSP
    python main.py --source 0                   # Use webcam
    python main.py --api-only                   # Run only the API server
"""

import argparse
import asyncio
import sys
import signal
import time
from pathlib import Path
from loguru import logger
import yaml

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:8}</level> | {message}")
logger.add("logs/traffic_cop.log", rotation="10 MB", retention="7 days", level="DEBUG")

# Import system modules
from src.input_layer.camera_feed import CameraFeed
from src.input_layer.frame_processor import FrameProcessor
from src.vision_layer.detector import ObjectDetector
from src.tracking_layer.tracker import VehicleTracker
from src.speed_estimation.speed_calculator import SpeedCalculator
from src.violation_detection.violation_detector import ViolationDetector
from src.decision_engine.decision_maker import DecisionMaker
from src.alerts.alert_manager import AlertManager


class TrafficCopSystem:
    """
    Main system orchestrator.
    Connects all layers into a cohesive real-time pipeline.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the AI Traffic Cop System.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.is_running = False
        self.frame_count = 0
        self.start_time = 0
        
        # Initialize all layers
        logger.info("🚔 Initializing AI Traffic Cop System...")
        
        self.camera = CameraFeed(
            source=self.config["camera"]["source"],
            resolution=(
                self.config["camera"]["resolution"]["width"],
                self.config["camera"]["resolution"]["height"]
            ),
            fps=self.config["camera"]["fps"],
            buffer_size=self.config["camera"]["buffer_size"],
        )
        
        self.frame_processor = FrameProcessor(
            target_size=(
                self.config["detection"]["img_size"],
                self.config["detection"]["img_size"]
            ),
        )
        
        self.detector = ObjectDetector(
            model_path=self.config["detection"]["model_path"],
            confidence=self.config["detection"]["confidence_threshold"],
            iou_threshold=self.config["detection"]["iou_threshold"],
            device=self.config["detection"]["device"],
            img_size=self.config["detection"]["img_size"],
        )
        
        self.tracker = VehicleTracker(
            max_age=self.config["tracking"]["max_age"],
            min_hits=self.config["tracking"]["min_hits"],
            iou_threshold=self.config["tracking"]["iou_threshold"],
            max_cosine_distance=self.config["tracking"]["max_cosine_distance"],
            nn_budget=self.config["tracking"]["nn_budget"],
            embedder=self.config["tracking"]["embedder"],
        )
        
        self.speed_calculator = SpeedCalculator(
            pixel_to_meter_ratio=self.config["speed_estimation"]["pixel_to_meter_ratio"],
            fps=self.config["speed_estimation"]["fps"],
            speed_limit=self.config["speed_estimation"]["speed_limit"],
            smoothing_window=self.config["speed_estimation"]["smoothing_window"],
            min_track_length=self.config["speed_estimation"]["min_track_length"],
        )
        
        self.violation_detector = ViolationDetector(
            config=self.config["violations"]
        )
        
        self.decision_maker = DecisionMaker(
            config=self.config.get("decision")
        )
        
        self.alert_manager = AlertManager(
            config=self.config.get("alerts")
        )
        
        logger.info("✅ All system components initialized")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return self._default_config()
        
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Configuration loaded from: {config_path}")
        return config
    
    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "camera": {
                "source": "0",
                "resolution": {"width": 1280, "height": 720},
                "fps": 30,
                "buffer_size": 10,
            },
            "detection": {
                "model_path": "models/yolov8n.pt",
                "confidence_threshold": 0.5,
                "iou_threshold": 0.45,
                "device": "auto",
                "img_size": 640,
            },
            "tracking": {
                "max_age": 30,
                "min_hits": 3,
                "iou_threshold": 0.3,
                "max_cosine_distance": 0.4,
                "nn_budget": 100,
                "embedder": "mobilenet",
            },
            "speed_estimation": {
                "pixel_to_meter_ratio": 0.05,
                "fps": 30,
                "speed_limit": 60,
                "smoothing_window": 5,
                "min_track_length": 10,
            },
            "violations": {
                "speed": {"enabled": True, "limit": 60, "tolerance": 5},
                "red_light": {"enabled": True, "crossing_line_y": 400},
                "lane": {"enabled": True, "lane_boundaries": [200, 400, 600, 800]},
                "parking": {"enabled": True, "max_stationary_time": 30, "forbidden_zones": []},
            },
            "decision": None,
            "alerts": {},
        }
    
    def run(self, source: str = None):
        """
        Run the main processing pipeline.
        
        Args:
            source: Override video source (optional)
        """
        if source:
            self.camera.source = source
        
        logger.info(f"🎬 Starting pipeline with source: {self.camera.source}")
        
        # Start camera
        if not self.camera.start():
            logger.error("Failed to start camera. Exiting.")
            return
        
        self.is_running = True
        self.start_time = time.time()
        
        logger.info("🟢 System running. Press Ctrl+C to stop.")
        
        try:
            self._processing_loop()
        except KeyboardInterrupt:
            logger.info("\n⛔ Interrupted by user")
        finally:
            self.stop()
    
    def _processing_loop(self):
        """Main frame processing loop."""
        import cv2
        
        for frame, timestamp in self.camera.get_frames():
            if not self.is_running:
                break
            
            self.frame_count += 1
            
            # Step 1: Detect objects
            detections = self.detector.detect(frame)
            
            # Step 2: Track vehicles
            tracks = self.tracker.update(detections, frame)
            
            # Step 3: Estimate speeds
            self.speed_calculator.update_all_tracks(tracks)
            
            # Step 4: Detect violations
            violations = self.violation_detector.detect_violations(
                tracks, frame, detections
            )
            
            # Step 5: Process violations through decision engine
            for violation in violations:
                decision = self.decision_maker.process_violation(violation)
                
                # Step 6: Send alerts if needed
                if decision.get("status") == "confirmed":
                    if "alert" in decision.get("actions", []):
                        asyncio.run(
                            self.alert_manager.send_alert(violation.to_dict())
                        )
            
            # Draw visualizations
            annotated_frame = self._draw_frame(frame, tracks, violations)
            
            # Display (if not headless)
            cv2.imshow("AI Traffic Cop System", annotated_frame)
            
            # Check for quit key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # Log progress periodically
            if self.frame_count % 100 == 0:
                fps = self.frame_count / (time.time() - self.start_time)
                active_tracks = self.tracker.get_vehicle_count()
                total_violations = len(self.violation_detector.violations)
                logger.info(
                    f"Frame {self.frame_count} | "
                    f"FPS: {fps:.1f} | "
                    f"Vehicles: {active_tracks} | "
                    f"Violations: {total_violations}"
                )
    
    def _draw_frame(self, frame, tracks, violations):
        """Draw tracking info and violations on frame."""
        import cv2
        
        annotated = frame.copy()
        
        # Draw tracks
        for track in tracks:
            x1, y1, x2, y2 = track.bbox
            
            # Color based on speed
            if track.current_speed > self.config["speed_estimation"]["speed_limit"]:
                color = (0, 0, 255)  # Red for speeding
            else:
                color = (0, 255, 0)  # Green for normal
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"ID:{track.track_id} {track.current_speed:.0f}km/h"
            cv2.putText(
                annotated, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
            )
            
            # Draw trail
            if len(track.positions) > 1:
                for i in range(1, min(len(track.positions), 20)):
                    pt1 = track.positions[i-1]
                    pt2 = track.positions[i]
                    cv2.line(annotated, pt1, pt2, color, 1)
        
        # Draw violation alerts
        for violation in violations:
            cv2.putText(
                annotated,
                f"⚠️ {violation.violation_type.value.upper()}",
                (10, 30 + violations.index(violation) * 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
            )
        
        # Draw info bar
        info = (
            f"Vehicles: {self.tracker.get_vehicle_count()} | "
            f"Violations: {len(self.violation_detector.violations)} | "
            f"Frame: {self.frame_count}"
        )
        cv2.putText(
            annotated, info, (10, annotated.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
        )
        
        return annotated
    
    def stop(self):
        """Stop the system and cleanup."""
        self.is_running = False
        self.camera.stop()
        
        import cv2
        cv2.destroyAllWindows()
        
        # Print summary
        elapsed = time.time() - self.start_time if self.start_time else 0
        logger.info("\n" + "=" * 50)
        logger.info("📊 SESSION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Duration: {elapsed:.1f}s")
        logger.info(f"Frames processed: {self.frame_count}")
        logger.info(f"Average FPS: {self.frame_count / elapsed:.1f}" if elapsed > 0 else "N/A")
        logger.info(f"Total violations: {len(self.violation_detector.violations)}")
        logger.info(f"Tracker stats: {self.tracker.get_statistics()}")
        logger.info("=" * 50)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="🚔 AI Traffic Cop System - Smart Traffic Enforcement"
    )
    parser.add_argument(
        "--source", type=str, default=None,
        help="Video source: file path, RTSP URL, or camera index"
    )
    parser.add_argument(
        "--config", type=str, default="config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--api-only", action="store_true",
        help="Run only the API server (no video processing)"
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0",
        help="API server host"
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="API server port"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    logger.info("🚔 AI Traffic Cop System v1.0.0")
    logger.info("=" * 50)
    
    if args.api_only:
        # Run only the API server
        logger.info("Starting in API-only mode...")
        from src.backend.app import run_server
        run_server(host=args.host, port=args.port)
    else:
        # Run full system
        system = TrafficCopSystem(config_path=args.config)
        
        # Handle graceful shutdown
        def signal_handler(sig, frame):
            logger.info("\n🛑 Shutting down...")
            system.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start processing
        system.run(source=args.source)


if __name__ == "__main__":
    main()
