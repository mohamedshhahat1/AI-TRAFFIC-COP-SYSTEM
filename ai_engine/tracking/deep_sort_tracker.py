"""
DeepSORT Tracker Module
Multi-object tracking with re-identification for persistent vehicle IDs.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("deep_sort_tracker")
except ImportError:
    from loguru import logger
import time

try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
except ImportError:
    DeepSort = None
    logger.warning("deep-sort-realtime not installed")

from .object_tracker import TrackedObject


class DeepSortTracker:
    """
    DeepSORT-based multi-object tracker.
    Assigns persistent IDs to vehicles across video frames.
    """
    
    def __init__(
        self,
        max_age: int = 30,
        min_hits: int = 5,  # Need 5 consecutive detections before confirming a track
        iou_threshold: float = 0.2,  # Lower = more lenient matching (less ID switches)
        max_cosine_distance: float = 0.6,  # Higher = more lenient appearance matching
        nn_budget: int = 100,
        embedder: str = "mobilenet",
    ):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        
        self.tracks: Dict[int, TrackedObject] = {}
        self.next_id = 1
        self.frame_count = 0
        
        # Initialize DeepSORT
        self._tracker = None
        if DeepSort is not None:
            try:
                self._tracker = DeepSort(
                    max_age=max_age,
                    n_init=min_hits,
                    max_iou_distance=1 - iou_threshold,
                    max_cosine_distance=max_cosine_distance,
                    nn_budget=nn_budget,
                    embedder=embedder,
                    half=True,
                    embedder_gpu=True,
                )
                logger.info(f"DeepSORT initialized | embedder={embedder}")
            except Exception as e:
                logger.warning(f"DeepSORT fallback to IoU: {e}")
                self._tracker = None
        
        if self._tracker is None:
            logger.info("Using IoU-based fallback tracker")
    
    def update(self, detections: list, frame: np.ndarray) -> List[TrackedObject]:
        """
        Update tracker with new frame detections.
        
        Args:
            detections: List of Detection objects
            frame: Current BGR frame
            
        Returns:
            List of active TrackedObject instances
        """
        self.frame_count += 1
        
        if not detections:
            for t in self.tracks.values():
                t.mark_missing()
            self._cleanup()
            return self.get_active()
        
        if self._tracker:
            return self._update_deepsort(detections, frame)
        return self._update_iou(detections)
    
    def _update_deepsort(self, detections: list, frame: np.ndarray) -> List[TrackedObject]:
        """Update using DeepSORT."""
        bbs = []
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            bbs.append(([x1, y1, x2 - x1, y2 - y1], det.confidence, det.class_name))
        
        tracked = self._tracker.update_tracks(bbs, frame=frame)
        active_ids = set()
        
        for obj in tracked:
            if not obj.is_confirmed():
                continue
            
            tid = obj.track_id
            active_ids.add(tid)
            ltrb = obj.to_ltrb()
            bbox = (int(ltrb[0]), int(ltrb[1]), int(ltrb[2]), int(ltrb[3]))
            cls = obj.det_class if hasattr(obj, 'det_class') and obj.det_class else "vehicle"
            conf = obj.det_conf if obj.det_conf else 0.5
            
            if tid not in self.tracks:
                self.tracks[tid] = TrackedObject(
                    track_id=tid, class_name=cls,
                    bbox=bbox, confidence=conf,
                )
            self.tracks[tid].update(bbox, conf)
        
        for tid, t in self.tracks.items():
            if tid not in active_ids:
                t.mark_missing()
        
        self._cleanup()
        return self.get_active()
    
    def _update_iou(self, detections: list) -> List[TrackedObject]:
        """Fallback IoU-based tracking."""
        matched_tracks = set()
        matched_dets = set()
        
        for i, det in enumerate(detections):
            best_iou, best_tid = 0.0, None
            for tid, t in self.tracks.items():
                if tid in matched_tracks:
                    continue
                iou = self._iou(det.bbox, t.bbox)
                if iou > best_iou and iou > self.iou_threshold:
                    best_iou, best_tid = iou, tid
            
            if best_tid is not None:
                self.tracks[best_tid].update(det.bbox, det.confidence)
                matched_tracks.add(best_tid)
                matched_dets.add(i)
        
        # New tracks
        for i, det in enumerate(detections):
            if i not in matched_dets:
                tid = self.next_id
                self.next_id += 1
                self.tracks[tid] = TrackedObject(
                    track_id=tid, class_name=det.class_name,
                    bbox=det.bbox, confidence=det.confidence,
                )
        
        for tid in self.tracks:
            if tid not in matched_tracks:
                self.tracks[tid].mark_missing()
        
        self._cleanup()
        return self.get_active()
    
    def _iou(self, b1, b2) -> float:
        """Compute IoU between two boxes."""
        x1 = max(b1[0], b2[0])
        y1 = max(b1[1], b2[1])
        x2 = min(b1[2], b2[2])
        y2 = min(b1[3], b2[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
        a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
        union = a1 + a2 - inter
        return inter / union if union > 0 else 0
    
    def _cleanup(self):
        """Remove dead tracks."""
        dead = [tid for tid, t in self.tracks.items() if t.frames_missing > self.max_age]
        for tid in dead:
            self.tracks[tid].is_active = False
            del self.tracks[tid]
    
    def get_active(self) -> List[TrackedObject]:
        """Get all active tracks."""
        return [t for t in self.tracks.values() if t.is_active]
    
    def get_count(self) -> int:
        """Active vehicle count."""
        return len(self.get_active())
    
    def get_stats(self) -> dict:
        active = self.get_active()
        classes = {}
        for t in active:
            classes[t.class_name] = classes.get(t.class_name, 0) + 1
        return {
            "active_tracks": len(active),
            "total_assigned": self.next_id - 1,
            "frame_count": self.frame_count,
            "class_distribution": classes,
        }
    
    def reset(self):
        """Reset tracker state."""
        self.tracks.clear()
        self.frame_count = 0
        if self._tracker:
            self._tracker.delete_all_tracks()
