"""
Bridge: Computer Vision Detections → RL State Vector.

Converts YOLO detection output (bounding boxes, classes, counts)
into the normalized state vector that the RL agent expects.

Flow:
    Camera Frame → YOLO Detector → Detections → Bridge → State Vector → RL Agent
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import time


@dataclass
class LaneConfig:
    """Configuration for a traffic lane's region of interest."""
    lane_id: str
    roi_polygon: List[Tuple[int, int]]  # Polygon defining the lane area in frame
    direction: str  # 'north', 'south', 'east', 'west'
    approach: str   # 'incoming' or 'outgoing'
    phase_group: int  # Which signal phase serves this lane (0-3)


@dataclass 
class LaneMetrics:
    """Real-time metrics for a single lane derived from CV."""
    queue_length: int = 0          # Halted vehicles (speed ≈ 0)
    vehicle_count: int = 0         # Total vehicles in lane
    avg_waiting_time: float = 0.0  # Estimated wait (seconds)
    density: float = 0.0           # Occupancy (0-1)
    flow_rate: float = 0.0         # Vehicles per minute
    avg_speed: float = 0.0         # km/h


class CVtoRLBridge:
    """
    Converts computer vision detections into RL state vectors.
    
    This bridge:
    1. Takes raw YOLO detections (bounding boxes + classes)
    2. Maps detections to lane ROIs (which lane is each vehicle in?)
    3. Estimates queue length, density, and waiting time per lane
    4. Normalizes into the state format expected by DQN/PPO agents
    
    Usage:
        bridge = CVtoRLBridge(lane_configs=[...], num_phases=4)
        
        # Each frame:
        detections = yolo_detector.detect(frame)
        state = bridge.detections_to_state(detections, current_phase=1)
        action = rl_agent.select_action(state)
    """
    
    def __init__(
        self,
        lane_configs: List[LaneConfig],
        num_phases: int = 4,
        frame_size: Tuple[int, int] = (1920, 1080),
        speed_threshold: float = 5.0,  # km/h below this = "stopped"
        history_window: int = 30,  # frames to average over
    ):
        """
        Initialize the CV→RL bridge.
        
        Args:
            lane_configs: List of lane ROI configurations
            num_phases: Number of signal phases
            frame_size: Camera frame dimensions (width, height)
            speed_threshold: Speed below which vehicle is "queued"
            history_window: Number of frames for temporal smoothing
        """
        self.lane_configs = lane_configs
        self.num_phases = num_phases
        self.num_lanes = len(lane_configs)
        self.frame_size = frame_size
        self.speed_threshold = speed_threshold
        self.history_window = history_window
        
        # State size matches TrafficSignalEnv format:
        # queue(N) + wait_time(N) + phase(P) + duration(1) + approaching(N) + density(N)
        self.state_size = self.num_lanes * 4 + num_phases + 1
        
        # Per-lane metric history for temporal smoothing
        self._lane_histories: Dict[str, deque] = {
            lc.lane_id: deque(maxlen=history_window)
            for lc in lane_configs
        }
        
        # Tracking state for waiting time estimation
        self._vehicle_first_seen: Dict[int, float] = {}  # track_id → timestamp
        self._vehicle_lane: Dict[int, str] = {}  # track_id → lane_id
        
        # Current phase tracking
        self._current_phase = 0
        self._phase_start_time = time.time()
        
        # Normalization constants
        self.MAX_QUEUE = 50.0
        self.MAX_WAIT = 200.0
        self.MAX_VEHICLES = 30.0
        self.MAX_GREEN_DURATION = 60.0
    
    def detections_to_state(
        self,
        detections: List,
        current_phase: int,
        tracked_objects: Optional[List] = None,
        speeds: Optional[Dict[int, float]] = None,
    ) -> np.ndarray:
        """
        Convert raw detections into normalized RL state vector.
        
        Args:
            detections: List of Detection objects from YOLODetector
            current_phase: Current signal phase index (0 to num_phases-1)
            tracked_objects: Optional tracked objects with IDs for waiting estimation
            speeds: Optional dict of {track_id: speed_kmh} from speed estimator
            
        Returns:
            Normalized state vector (shape: state_size,)
        """
        # Update phase tracking
        if current_phase != self._current_phase:
            self._current_phase = current_phase
            self._phase_start_time = time.time()
        
        # Calculate per-lane metrics
        lane_metrics = self._compute_lane_metrics(detections, tracked_objects, speeds)
        
        # Build state vector
        queue_lengths = np.array([
            lane_metrics[lc.lane_id].queue_length / self.MAX_QUEUE
            for lc in self.lane_configs
        ], dtype=np.float32)
        
        waiting_times = np.array([
            lane_metrics[lc.lane_id].avg_waiting_time / self.MAX_WAIT
            for lc in self.lane_configs
        ], dtype=np.float32)
        
        # Current phase one-hot
        phase_one_hot = np.zeros(self.num_phases, dtype=np.float32)
        phase_one_hot[current_phase] = 1.0
        
        # Phase duration (normalized)
        phase_duration = np.array([
            (time.time() - self._phase_start_time) / self.MAX_GREEN_DURATION
        ], dtype=np.float32)
        
        # Approaching vehicles (total in each lane)
        approaching = np.array([
            lane_metrics[lc.lane_id].vehicle_count / self.MAX_VEHICLES
            for lc in self.lane_configs
        ], dtype=np.float32)
        
        # Density
        density = np.array([
            lane_metrics[lc.lane_id].density
            for lc in self.lane_configs
        ], dtype=np.float32)
        
        # Concatenate and clip
        state = np.concatenate([
            np.clip(queue_lengths, 0, 1),
            np.clip(waiting_times, 0, 1),
            phase_one_hot,
            np.clip(phase_duration, 0, 1),
            np.clip(approaching, 0, 1),
            np.clip(density, 0, 1),
        ])
        
        return state.astype(np.float32)
    
    def _compute_lane_metrics(
        self,
        detections: List,
        tracked_objects: Optional[List],
        speeds: Optional[Dict[int, float]],
    ) -> Dict[str, LaneMetrics]:
        """Compute metrics for each lane from detections."""
        metrics = {lc.lane_id: LaneMetrics() for lc in self.lane_configs}
        
        # Filter to vehicle detections only
        vehicle_classes = {"car", "truck", "bus", "motorcycle"}
        vehicles = [d for d in detections if getattr(d, 'class_name', '') in vehicle_classes]
        
        # Assign each vehicle to a lane based on its center point
        for vehicle in vehicles:
            center = getattr(vehicle, 'center', (0, 0))
            lane = self._point_to_lane(center)
            
            if lane:
                metrics[lane].vehicle_count += 1
                
                # Check if vehicle is stopped (queued)
                track_id = getattr(vehicle, 'track_id', None)
                if speeds and track_id and track_id in speeds:
                    if speeds[track_id] < self.speed_threshold:
                        metrics[lane].queue_length += 1
                else:
                    # No speed info: estimate from position (bottom of ROI = likely queued)
                    # Simple heuristic: if in bottom 40% of lane ROI, probably queued
                    metrics[lane].queue_length += 1  # Conservative: count all as queued
        
        # Calculate density for each lane
        for lc in self.lane_configs:
            m = metrics[lc.lane_id]
            max_capacity = 15  # Approximate max vehicles per lane segment
            m.density = min(m.vehicle_count / max_capacity, 1.0)
        
        # Estimate waiting times from tracked objects
        if tracked_objects:
            current_time = time.time()
            for obj in tracked_objects:
                track_id = getattr(obj, 'track_id', getattr(obj, 'id', None))
                if track_id is None:
                    continue
                
                center = getattr(obj, 'center', getattr(obj, 'position', (0, 0)))
                lane = self._point_to_lane(center)
                
                if lane:
                    # Track when we first saw this vehicle
                    if track_id not in self._vehicle_first_seen:
                        self._vehicle_first_seen[track_id] = current_time
                        self._vehicle_lane[track_id] = lane
                    
                    # Calculate waiting time
                    wait = current_time - self._vehicle_first_seen[track_id]
                    
                    # Only count if vehicle is in a stopped/queued state
                    speed = speeds.get(track_id, 0) if speeds else 0
                    if speed < self.speed_threshold:
                        metrics[lane].avg_waiting_time = max(
                            metrics[lane].avg_waiting_time, wait
                        )
            
            # Clean up old tracks (not seen in last 10 seconds)
            stale_tracks = [
                tid for tid, t in self._vehicle_first_seen.items()
                if current_time - t > 30
            ]
            for tid in stale_tracks:
                self._vehicle_first_seen.pop(tid, None)
                self._vehicle_lane.pop(tid, None)
        
        return metrics
    
    def _point_to_lane(self, point: Tuple[int, int]) -> Optional[str]:
        """
        Determine which lane a point belongs to using ROI polygons.
        
        Uses cv2.pointPolygonTest or simple bounding box check.
        """
        x, y = point
        
        for lc in self.lane_configs:
            # Simple bounding box check from polygon
            xs = [p[0] for p in lc.roi_polygon]
            ys = [p[1] for p in lc.roi_polygon]
            
            if min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys):
                return lc.lane_id
        
        return None
    
    def get_metrics_summary(self) -> Dict:
        """Get current metrics for dashboard display."""
        return {
            "num_lanes": self.num_lanes,
            "current_phase": self._current_phase,
            "phase_duration": time.time() - self._phase_start_time,
            "tracked_vehicles": len(self._vehicle_first_seen),
            "state_size": self.state_size,
        }
    
    @staticmethod
    def create_default_4way(frame_width: int = 1920, frame_height: int = 1080) -> 'CVtoRLBridge':
        """
        Create a bridge with default 4-way intersection lane configuration.
        Divides the frame into 4 quadrants for N/S/E/W approaches.
        """
        w, h = frame_width, frame_height
        cx, cy = w // 2, h // 2
        
        lanes = [
            # North approach (top center, coming down)
            LaneConfig("N_in_0", [(cx-100,0),(cx,0),(cx,cy-50),(cx-100,cy-50)], "north", "incoming", 0),
            LaneConfig("N_in_1", [(cx,0),(cx+100,0),(cx+100,cy-50),(cx,cy-50)], "north", "incoming", 0),
            # South approach (bottom center, coming up)
            LaneConfig("S_in_0", [(cx-100,cy+50),(cx,cy+50),(cx,h),(cx-100,h)], "south", "incoming", 0),
            LaneConfig("S_in_1", [(cx,cy+50),(cx+100,cy+50),(cx+100,h),(cx,h)], "south", "incoming", 0),
            # East approach (right center, going left)
            LaneConfig("E_in_0", [(cx+50,cy-100),(w,cy-100),(w,cy),(cx+50,cy)], "east", "incoming", 2),
            LaneConfig("E_in_1", [(cx+50,cy),(w,cy),(w,cy+100),(cx+50,cy+100)], "east", "incoming", 2),
            # West approach (left center, going right)
            LaneConfig("W_in_0", [(0,cy-100),(cx-50,cy-100),(cx-50,cy),(0,cy)], "west", "incoming", 2),
            LaneConfig("W_in_1", [(0,cy),(cx-50,cy),(cx-50,cy+100),(0,cy+100)], "west", "incoming", 2),
        ]
        
        return CVtoRLBridge(
            lane_configs=lanes,
            num_phases=4,
            frame_size=(w, h),
        )
