"""
Video Processor - Background task that feeds video frames to the AI Gateway.
Results are automatically broadcast to all WebSocket clients (dashboard).
"""

import asyncio
import threading
import cv2
import time
from pathlib import Path

try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("video_processor")
except (ImportError, Exception):
    from loguru import logger


class VideoProcessor:
    """Processes video in a background thread and pushes results to the API."""
    
    def __init__(self, gateway, broadcast_fn):
        self.gateway = gateway
        self.broadcast = broadcast_fn
        self._thread = None
        self._running = False
        self._source = None
        self._loop = None
        self.stats = {"fps": 0, "objects": 0, "frame": 0, "violations": 0}
        self.camera_info = {"source": "", "name": "No camera", "resolution": "—", "fps": 0, "status": "Disconnected"}
        self._latest_frame = None  # Latest annotated frame (JPEG bytes)
        self.detection_counts = {"car": 0, "truck": 0, "motorcycle": 0, "bus": 0, "person": 0, "traffic_light": 0, "bicycle": 0}
        self._confidence_sum = 0.0
        self._confidence_count = 0
    
    def start(self, source: str = "data/videos/traffic.mp4"):
        """Start processing video in background thread."""
        if self._running:
            return {"status": "already_running"}
        
        self._source = source
        self._running = True
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.get_event_loop()
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        
        logger.info(f"Video processing started: {source}")
        return {"status": "started", "source": source}
    
    def stop(self):
        """Stop video processing."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("Video processing stopped")
        return {"status": "stopped"}
    
    def _process_loop(self):
        """Background video processing loop."""
        cap = cv2.VideoCapture(self._source)
        
        if not cap.isOpened():
            logger.error(f"Cannot open video: {self._source}")
            self._running = False
            return
        
        # Get camera/video info
        self.camera_info = {
            "source": self._source,
            "name": self._source.split("/")[-1] if "/" in self._source else f"CAM_{self._source}",
            "resolution": f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}",
            "fps": int(cap.get(cv2.CAP_PROP_FPS)),
            "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "status": "Connected",
        }
        
        fps_counter = 0
        fps_start = time.time()
        
        while self._running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                # Loop video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            # Process frame through AI Pipeline directly (raw objects for annotation)
            if self.gateway.inference._pipeline:
                results = self.gateway.inference._pipeline.process_frame(frame)
            else:
                results = self.gateway.process_frame(frame)
            fps_counter += 1
            
            # Calculate FPS
            elapsed = time.time() - fps_start
            if elapsed >= 1.0:
                current_fps = fps_counter / elapsed
                fps_counter = 0
                fps_start = time.time()
            else:
                current_fps = self.stats["fps"]
            
            # Extract stats - handle both pipeline and formatted response
            stats = results.get("stats", results)
            detections = stats.get("detected_objects", 0) or results.get("detections", {}).get("count", 0)
            tracks_val = stats.get("active_tracks", 0) or results.get("tracking", {}).get("active_vehicles", 0)
            violations_val = stats.get("new_violations", 0) or results.get("violations", {}).get("new_count", 0)
            
            # Count detections by class
            raw_dets = results.get("detections", [])
            if isinstance(raw_dets, dict):
                raw_dets = raw_dets.get("objects", [])
            for d in raw_dets:
                cls_name = d.class_name if hasattr(d, "class_name") else d.get("class", "")
                if cls_name in self.detection_counts:
                    self.detection_counts[cls_name] += 1
                # Track avg detection confidence (NOT accuracy — that requires Ground Truth)
                conf = d.confidence if hasattr(d, "confidence") else d.get("confidence", 0)
                if conf > 0:
                    self._confidence_sum += conf
                    self._confidence_count += 1

            self.stats = {
                "fps": round(current_fps, 1),
                "objects": detections,
                "tracks": tracks_val,
                "frame": results.get("frame_number", 0) or stats.get("frame_number", 0),
                "violations": violations_val,
                "congestion": stats.get("congestion_level", "free") or results.get("congestion", {}).get("level", "free"),
                "health_score": stats.get("health_score", 100),
                "detection_counts": self.detection_counts,
                "avg_confidence": round(self._confidence_sum / max(self._confidence_count, 1) * 100, 1),
            }
            
            # Annotate frame with bounding boxes, IDs, speed, violations
            annotated = self._annotate_frame(frame, results)
            
            # Encode as JPEG for streaming
            _, jpeg = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
            self._latest_frame = jpeg.tobytes()
            
            # Broadcast to WebSocket clients
            self._send_update({
                "type": "frame_update",
                "data": self.stats
            })
            
            # Broadcast violations
            raw_violations = results.get("violations", [])
            if isinstance(raw_violations, dict):
                raw_violations = raw_violations.get("items", [])
            for v in raw_violations:
                v_data = v.to_dict() if hasattr(v, 'to_dict') else v
                self._send_update({
                    "type": "violation",
                    "data": v_data
                })
            
            # Broadcast accident risks
            raw_risks = results.get("accident_risks", [])
            if isinstance(raw_risks, dict):
                raw_risks = raw_risks.get("items", [])
            for r in raw_risks:
                if hasattr(r, 'risk_level'):
                    self._send_update({"type": "accident_risk", "data": {
                        "level": r.risk_level,
                        "score": r.risk_score,
                        "vehicles": r.involved_vehicles,
                        "ttc": r.time_to_collision,
                        "description": r.description if hasattr(r, 'description') else "",
                    }})
                elif isinstance(r, dict):
                    self._send_update({"type": "accident_risk", "data": r})
            
            # No throttle - pipeline speed is the natural limit on CPU
        
        cap.release()
        self._running = False
    
    def _annotate_frame(self, frame, results):
        """Draw bounding boxes, IDs, speed, and violations on frame."""
        annotated = frame.copy()
        
        # Get tracks, detections, and violations
        tracks = results.get("tracks", [])
        detections = results.get("detections", [])
        violations = results.get("violations", [])
        violation_track_ids = set()
        
        # Collect violation track IDs
        raw_violations = violations
        if isinstance(raw_violations, dict):
            raw_violations = raw_violations.get("items", [])
        for v in raw_violations:
            tid = v.track_id if hasattr(v, 'track_id') else v.get('track_id', -1)
            violation_track_ids.add(tid)
        
        # Draw tracked vehicles (with ID + speed)
        for track in tracks:
            # Handle both raw Track objects and dicts
            if hasattr(track, 'bbox'):
                x1, y1, x2, y2 = track.bbox
                speed = track.current_speed
                tid = track.track_id
                cls = track.class_name
            elif isinstance(track, dict):
                bbox = track.get('bbox', (0,0,0,0))
                x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                speed = track.get('speed', 0)
                tid = track.get('track_id', '?')
                cls = track.get('class_name', 'vehicle')
            else:
                continue
            
            is_violating = tid in violation_track_ids
            color = (0, 0, 255) if is_violating else (0, 255, 0)
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            label = f"{cls} #{tid}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            speed_label = f"{speed:.0f} km/h"
            cv2.putText(annotated, speed_label, (x1, y2 + 16),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
            
            if is_violating:
                cv2.putText(annotated, "!! VIOLATION", (x1, y2 + 32),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
        
        # FALLBACK: If no tracks but detections exist, draw raw detections
        # This ensures bounding boxes are ALWAYS visible when YOLO detects something
        if not tracks and detections:
            raw_dets = detections
            if isinstance(raw_dets, dict):
                raw_dets = raw_dets.get("objects", [])
            for i, det in enumerate(raw_dets):
                if hasattr(det, 'bbox'):
                    x1, y1, x2, y2 = det.bbox
                    cls_name = det.class_name
                    conf = det.confidence
                elif isinstance(det, dict):
                    bbox = det.get('bbox', (0,0,0,0))
                    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                    cls_name = det.get('class', det.get('class_name', ''))
                    conf = det.get('confidence', 0)
                else:
                    continue
                
                color = (0, 255, 255)  # Yellow for untracked detections
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                label = f"{cls_name} {conf:.0%}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(annotated, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 3),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
        
        # Draw violation alerts on top
        y_offset = 30
        for v in raw_violations[:3]:
            v_type = v.type.value if hasattr(v, 'type') else v.get('type', '')
            v_tid = v.track_id if hasattr(v, 'track_id') else v.get('track_id', '?')
            text = f"!! {v_type}: Vehicle #{v_tid}"
            cv2.putText(annotated, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            y_offset += 25
        
        # Info bar at bottom
        h, w = annotated.shape[:2]
        detected_count = len(tracks) if tracks else len([d for d in (detections if not isinstance(detections, dict) else []) if hasattr(d, 'bbox')])
        cv2.rectangle(annotated, (0, h - 30), (w, h), (0, 0, 0), -1)
        info = f"AI Traffic Cop | Vehicles: {detected_count} | FPS: {self.stats.get('fps', 0)} | Frame: {self.stats.get('frame', 0)}"
        cv2.putText(annotated, info, (10, h - 8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        
        return annotated

    def get_frame(self):
        """Get latest annotated frame as JPEG bytes."""
        return self._latest_frame

    def _send_update(self, data):
        """Thread-safe broadcast to WebSocket clients."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(
                asyncio.ensure_future, self.broadcast(data)
            )
    
    @property
    def is_running(self):
        return self._running
