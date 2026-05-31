"""
Run Pipeline Script
Quick launcher for the AI Traffic Cop System.
Uses the AIGateway (API Bridge) for clean architecture.
Events are emitted through the Event Bus automatically.
"""

import sys
import argparse
sys.path.insert(0, '.')

from ai_engine.api_bridge import AIGateway
from ai_engine.event_bus import EventManager, TrafficEvent
import cv2
from loguru import logger
import yaml


def main():
    parser = argparse.ArgumentParser(description="🚔 AI Traffic Cop - Run Pipeline")
    parser.add_argument("--source", default="data/videos/sample.mp4", help="Video source")
    parser.add_argument("--config", default="configs/settings.yaml", help="Config file")
    parser.add_argument("--display", action="store_true", help="Show video window")
    args = parser.parse_args()
    
    # Load config
    try:
        with open(args.config) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}
    
    # Initialize AI Gateway (single entry point)
    gateway = AIGateway(config)
    
    # Subscribe to events (example: log violations to console)
    gateway.on_violation(lambda v: logger.warning(f"🚨 VIOLATION: {v}"))
    gateway.on_accident_risk(lambda r: logger.error(f"⚠️ ACCIDENT RISK: {r}"))
    gateway.on_congestion_change(lambda c: logger.info(f"🚦 CONGESTION: {c}"))
    
    # Start the AI services
    gateway.start()
    
    # Open video
    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        logger.error(f"Cannot open source: {args.source}")
        return
    
    logger.info(f"🎬 Processing: {args.source}")
    
    frame_count = 0
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame through AI Gateway
            results = gateway.process_frame(frame)
            frame_count += 1
            
            if args.display:
                # Annotate frame using pipeline
                if gateway.inference._pipeline:
                    annotated = gateway.inference._pipeline.annotate_frame(frame, results)
                    cv2.imshow("AI Traffic Cop", annotated)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            
            if frame_count % 100 == 0:
                metrics = gateway.get_metrics()
                service = metrics.get("service", {})
                logger.info(
                    f"Frame {frame_count} | "
                    f"Inferences: {service.get('total_inferences', 0)} | "
                    f"Avg latency: {service.get('avg_latency_ms', 0):.0f}ms"
                )
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # Print final metrics
        metrics = gateway.get_metrics()
        health = gateway.health()
        logger.info(f"\n📊 Final Metrics: {metrics}")
        logger.info(f"🏥 Health: {health}")
        
        gateway.stop()


if __name__ == "__main__":
    main()
