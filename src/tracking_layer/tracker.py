"""
Vehicle Tracker Module
DeepSORT-based multi-object tracker for persistent vehicle identification.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from loguru import logger
import time

try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
except ImportError:
    logger.warning("deep-sort-realtime not installed. Run: pip install deep-sort-realtime")
    DeepSort = None

from .track import Track


class VehicleTracker:
    """
    Multi-object tracker using DeepSORT algorithm.
    
    Maintains persistent vehicle IDs across video frames,
    enabling speed estimation and violation tracking.
    """
    
    def __init__(
        self,
        max_age: int = 30,
        min_hits: int = 3,
        iou_threshold: float = 0.3,
        max_cosine_distance: float = 0.4,
        nn_budget: int = 100,
        embedder: str = "mobilenet"
    ):
        """
        Initialize the vehicle tracker.
        
        Args:
            max_age: Maximum frames to keep a track without detection
            min_hits: Minimum hits before track is confirmed
            iou_threshold: IoU threshold for matching
            max_cosine_distance: Max cosine distance for appearance matching
            nn_budget: Maximum size of feature gallery
            embedder: Feature extractor model (mobilenet, torchreid, clip_RN50)
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.max_cosine_distance = max_cosine_distance
        self.nn_budget = nn_budget
        
        # Active tracks
        self.tracks: Dict[int, Track] = {}
        self.next_id: int = 1
        self.frame_count: int = 0
        
        # Initialize DeepSORT
        self.tracker = None
        self._init_deepsort(embedder)
        
        logger.info("VehicleTracker initialized")
    
    def _init_deepsort(self, embedder: str):
        """Initialize DeepSORT tracker."""
        if DeepSort is None:
            logger.warning("DeepSORT not available, using basic IoU tracking")
            return
        
        try:
            self.tracker = DeepSort(
                max_age=self.max_age,
                n_init=self.min_hits,
                max_iou_distance=1 - self.iou_threshold,
                max_cosine_distance=self.max_cosine_distance,
                nn_budget=self.nn_budget,
                embedder=embedder,
                half=True,
                embedder_gpu=True,
            )
            logger.info(f"DeepSORT initialized with {embedder} embedder")
        except Exception as e:
            logger.warning(f"DeepSORT init failed: {e}. Using fallback tracker.")
            self.tracker = None
    
    def update(
        self, 
        detections: list, 
        frame: np.ndarray
    ) -> List[Track]:
        """
        Update tracker with new detections.
        
        Args:
            detections: List of Detection objects from the detector
            frame: Current video frame (for appearance features)
            
        Returns:
            List of active Track objects
        """
        self.frame_count += 1
        current_time = time.time()
        
        if not detections:
            # Mark all tracks as missed
            for track in self.tracks.values():
                track.mark_missed()
            self._cleanup_tracks()
            return list(self.tracks.values())
        
        if self.tracker is not None:
            return self._update_deepsort(detections, frame, current_time)
        else:
            return self._update_iou(detections, current_time)
    
    def _update_deepsort(
        self, 
        detections: list, 
        frame: np.ndarray,
        current_time: float
    ) -> List[Track]:
        """Update using DeepSORT algorithm."""
        # Format detections for DeepSORT: [[x1, y1, w, h, conf], ...]
        bbs = []
        det_classes = []
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            w = x2 - x1
            h = y2 - y1
            bbs.append(([x1, y1, w, h], det.confidence, det.class_name))
            det_classes.append(det.class_name)
        
        # Update DeepSORT tracker
        tracked_objects = self.tracker.update_tracks(bbs, frame=frame)
        
        # Update our track objects
        active_ids = set()
        
        for obj in tracked_objects:
            if not obj.is_confirmed():
                continue
            
            track_id = obj.track_id
            active_ids.add(track_id)
            
            ltrb = obj.to_ltrb()
            bbox = (int(ltrb[0]), int(ltrb[1]), int(ltrb[2]), int(ltrb[3]))
            
            # Get class name from detection
            det_class = obj.det_class if hasattr(obj, 'det_class') and obj.det_class else "vehicle"
            
            if track_id not in self.tracks:
                # New track
                self.tracks[track_id] = Track(
                    track_id=track_id,
                    class_name=det_class,
                    bbox=bbox,
                    confidence=obj.det_conf if obj.det_conf else 0.5,
                    first_seen=current_time
                )
            
            # Update existing track
            self.tracks[track_id].update(
                bbox=bbox,
                confidence=obj.det_conf if obj.det_conf else 0.5
            )
        
        # Mark unmatched tracks
        for tid, track in self.tracks.items():
            if tid not in active_ids:
                track.mark_missed()
        
        self._cleanup_tracks()
        
        return [t for t in self.tracks.values() if t.is_active]
    
    def _update_iou(
        self, 
        detections: list, 
        current_time: float
    ) -> List[Track]:
        """Fallback IoU-based tracking when DeepSORT is unavailable."""
        # Simple IoU matching
        matched_tracks = set()
        matched_dets = set()
        
        for det_idx, det in enumerate(detections):
            best_iou = 0
            best_track_id = None
            
            for tid, track in self.tracks.items():
                if tid in matched_tracks:
                    continue
                
                iou = self._compute_iou(det.bbox, track.bbox)
                if iou > best_iou and iou > self.iou_threshold:
                    best_iou = iou
                    best_track_id = tid
            
            if best_track_id is not None:
                self.tracks[best_track_id].update(det.bbox, det.confidence)
                matched_tracks.add(best_track_id)
                matched_dets.add(det_idx)
        
        # Create new tracks for unmatched detections
        for det_idx, det in enumerate(detections):
            if det_idx not in matched_dets:
                track_id = self.next_id
                self.next_id += 1
                self.tracks[track_id] = Track(
                    track_id=track_id,
                    class_name=det.class_name,
                    bbox=det.bbox,
                    confidence=det.confidence,
                    first_seen=current_time
                )
        
        # Mark unmatched tracks as missed
        for tid in self.tracks:
            if tid not in matched_tracks:
                self.tracks[tid].mark_missed()
        
        self._cleanup_tracks()
        
        return [t for t in self.tracks.values() if t.is_active]
    
    def _compute_iou(
        self, 
        bbox1: Tuple[int, int, int, int], 
        bbox2: Tuple[int, int, int, int]
    ) -> float:
        """Compute Intersection over Union between two bounding boxes."""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def _cleanup_tracks(self):
        """Remove stale tracks."""
        to_remove = []
        for tid, track in self.tracks.items():
            if track.frames_since_update > self.max_age:
                track.is_active = False
                to_remove.append(tid)
        
        for tid in to_remove:
            del self.tracks[tid]
    
    def get_track(self, track_id: int) -> Optional[Track]:
        """Get a specific track by ID."""
        return self.tracks.get(track_id)
    
    def get_active_tracks(self) -> List[Track]:
        """Get all currently active tracks."""
        return [t for t in self.tracks.values() if t.is_active]
    
    def get_vehicle_count(self) -> int:
        """Get current number of tracked vehicles."""
        return len([t for t in self.tracks.values() if t.is_active])
    
    def get_statistics(self) -> dict:
        """Get tracker statistics."""
        active = self.get_active_tracks()
        return {
            "total_tracks": len(self.tracks),
            "active_tracks": len(active),
            "frame_count": self.frame_count,
            "class_distribution": self._get_class_distribution(active),
        }
    
    def _get_class_distribution(self, tracks: List[Track]) -> Dict[str, int]:
        """Get distribution of tracked object classes."""
        dist = {}
        for track in tracks:
            dist[track.class_name] = dist.get(track.class_name, 0) + 1
        return dist
    
    def reset(self):
        """Reset the tracker."""
        self.tracks.clear()
        self.frame_count = 0
        if self.tracker:
            self.tracker.delete_all_tracks()
        logger.info("Tracker reset")
