"""
Run Pipeline Script
Quick launcher for the AI Traffic Cop System.
"""

import sys
import argparse
sys.path.insert(0, '.')

from ai_engine.pipeline import AIPipeline
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
    
    # Initialize pipeline
    pipeline = AIPipeline(config)
    
    # Open video
    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        logger.error(f"Cannot open source: {args.source}")
        return
    
    logger.info(f"🎬 Processing: {args.source}")
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            results = pipeline.process_frame(frame)
            
            if args.display:
                annotated = pipeline.annotate_frame(frame, results)
                cv2.imshow("AI Traffic Cop", annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            if pipeline.frame_count % 100 == 0:
                stats = results['stats']
                logger.info(
                    f"Frame {stats['detected_objects']} objects | "
                    f"{stats['active_tracks']} tracked | "
                    f"{stats['processing_time_ms']:.0f}ms"
                )
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        summary = pipeline.get_summary()
        logger.info(f"\n📊 Summary: {summary['frames_processed']} frames | "
                   f"{summary['total_violations']} violations | "
                   f"{summary['avg_fps']:.1f} FPS")


if __name__ == "__main__":
    main()
