"""
Video Processor - Background task that feeds video frames to the AI Gateway.
Results are automatically broadcast to all WebSocket clients (dashboard).
Violations are persisted to the database.
"""

import asyncio
import threading
import cv2
import time
import uuid
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
        self._total_violations = 0

    def start(self, source: str = "data/videos/traffic.mp4"):
        """Start processing video in background thread."""
        if self._running:
            return {"status": "already_running"}

        # Validate source path
        if not source.startswith("rtsp://") and not source.startswith("http"):
            source_path = Path(source)
            if not source_path.exists():
                return {"status": "error", "message": f"Video file not found: {source}"}

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
        """Stop video processing and reset all stats."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        # Reset all stats to zero
        self.stats = {"fps": 0, "objects": 0, "frame": 0, "violations": 0}
        self.detection_counts = {"car": 0, "truck": 0, "motorcycle": 0, "bus": 0, "person": 0, "traffic_light": 0, "bicycle": 0}
        self._confidence_sum = 0.0
        self._confidence_count = 0
        self._latest_frame = None
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
        video_fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        self.camera_info = {
            "source": self._source,
            "name": self._source.split("/")[-1] if "/" in self._source else f"CAM_{self._source}",
            "resolution": f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}",
            "fps": video_fps,
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

            # Process frame through AI Pipeline
            try:
                if self.gateway.inference._pipeline:
                    results = self.gateway.inference._pipeline.process_frame(frame)
                else:
                    results = self.gateway.process_frame(frame)
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
                continue

            fps_counter += 1

            # Calculate FPS
            elapsed = time.time() - fps_start
            if elapsed >= 1.0:
                current_fps = fps_counter / elapsed
                fps_counter = 0
                fps_start = time.time()
            else:
                current_fps = self.stats["fps"]

            # Extract stats from pipeline results
            stats = results.get("stats", {})
            detections = stats.get("detected_objects", 0)
            tracks_val = stats.get("active_tracks", 0) or results.get("tracking", {}).get("active_vehicles", 0)
            violations_list = results.get("violations", [])
            if isinstance(violations_list, dict):
                violations_list = violations_list.get("items", [])
            violations_val = len(violations_list) if isinstance(violations_list, list) else 0

            # Count detections by class
            raw_dets = results.get("detections", [])
            if isinstance(raw_dets, dict):
                raw_dets = raw_dets.get("objects", [])
            for d in raw_dets:
                cls_name = d.class_name if hasattr(d, "class_name") else d.get("class", "")
                if cls_name in self.detection_counts:
                    self.detection_counts[cls_name] += 1
                # Track avg detection confidence
                conf = d.confidence if hasattr(d, "confidence") else d.get("confidence", 0)
                if conf > 0:
                    self._confidence_sum += conf
                    self._confidence_count += 1

            # Calculate average speed from tracked vehicles
            raw_tracks = results.get("tracks", [])
            speeds = []
            for t in raw_tracks:
                spd = t.current_speed if hasattr(t, 'current_speed') else 0
                if spd > 0:
                    speeds.append(spd)
            avg_speed = round(sum(speeds) / len(speeds), 1) if speeds else 0

            self._total_violations += violations_val
            self.stats = {
                "fps": round(current_fps, 1),
                "objects": detections,
                "tracks": tracks_val,
                "avg_speed": avg_speed,
                "frame": results.get("frame_number", 0) or stats.get("frame_number", 0),
                "violations": self._total_violations,
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

            # Persist violations to database and broadcast
            for v in violations_list:
                v_data = v.to_dict() if hasattr(v, 'to_dict') else v
                self._send_update({
                    "type": "violation",
                    "data": v_data
                })
                # Persist to DB asynchronously
                self._persist_violation(v_data)

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

            # Persist tracked vehicles periodically (every 30 frames)
            frame_num = self.stats.get("frame", 0)
            if frame_num > 0 and frame_num % 30 == 0 and raw_tracks:
                self._persist_vehicles(raw_tracks)

        cap.release()
        self._running = False

    def _persist_violation(self, v_data: dict):
        """Persist a violation to the database (async, non-blocking)."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(
                asyncio.ensure_future, self._save_violation_to_db(v_data)
            )

    async def _save_violation_to_db(self, v_data: dict):
        """Save violation to database."""
        try:
            from .services.db_service import async_session
            from .models.violation_model import ViolationModel

            async with async_session() as session:
                violation = ViolationModel(
                    violation_id=v_data.get("id", str(uuid.uuid4())[:8]),
                    type=v_data.get("type", "unknown"),
                    severity=v_data.get("severity", "low"),
                    track_id=v_data.get("track_id", 0),
                    vehicle_class=v_data.get("vehicle_class", "unknown"),
                    speed=v_data.get("speed", 0.0),
                    speed_limit=v_data.get("speed_limit", 60.0),
                    description=v_data.get("description", ""),
                )
                session.add(violation)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to persist violation: {e}")

    def _persist_vehicles(self, tracks: list):
        """Persist tracked vehicles to the database (async, non-blocking)."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(
                asyncio.ensure_future, self._save_vehicles_to_db(tracks)
            )

    async def _save_vehicles_to_db(self, tracks: list):
        """Save or update tracked vehicles in database."""
        try:
            from .services.db_service import async_session
            from .models.vehicle_model import VehicleModel
            from sqlalchemy import select
            from datetime import datetime

            async with async_session() as session:
                for track in tracks[:50]:  # Limit batch size
                    track_id = track.track_id if hasattr(track, 'track_id') else track.get('track_id', 0)
                    if not track_id:
                        continue

                    result = await session.execute(
                        select(VehicleModel).where(VehicleModel.track_id == track_id)
                    )
                    vehicle = result.scalar_one_or_none()

                    speed = track.current_speed if hasattr(track, 'current_speed') else track.get('speed', 0)
                    cls = track.class_name if hasattr(track, 'class_name') else track.get('class_name', 'car')

                    if vehicle:
                        vehicle.current_speed = speed
                        vehicle.max_speed = max(vehicle.max_speed or 0, speed)
                        vehicle.last_seen = datetime.utcnow()
                        vehicle.is_active = True
                    else:
                        vehicle = VehicleModel(
                            track_id=track_id,
                            vehicle_class=cls,
                            current_speed=speed,
                            max_speed=speed,
                            avg_speed=speed,
                        )
                        session.add(vehicle)

                await session.commit()
        except Exception as e:
            logger.error(f"Failed to persist vehicles: {e}")

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

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)

            label = f"{cls} #{tid}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(annotated, (x1, y1 - th - 10), (x1 + tw + 6, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 3, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            speed_label = f"{speed:.0f} km/h"
            cv2.putText(annotated, speed_label, (x1, y2 + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            if is_violating:
                cv2.putText(annotated, "!! VIOLATION", (x1, y2 + 42),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # FALLBACK: Only draw raw detections if NO tracks exist at all
        if not tracks:
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

                color = (0, 255, 255)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)
                label = f"{cls_name} {conf:.0%}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # Draw violation alerts on top
        y_offset = 30
        for v in raw_violations[:3]:
            v_type = v.type.value if hasattr(v, 'type') and hasattr(v.type, 'value') else (v.type if hasattr(v, 'type') else v.get('type', ''))
            v_tid = v.track_id if hasattr(v, 'track_id') else v.get('track_id', '?')
            text = f"!! {v_type}: Vehicle #{v_tid}"
            cv2.putText(annotated, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
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
