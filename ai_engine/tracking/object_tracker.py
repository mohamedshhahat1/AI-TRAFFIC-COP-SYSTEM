"""
Object Tracker - Data structures for tracked objects.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import time


@dataclass
class TrackedObject:
    """Represents a single tracked vehicle/object."""
    
    track_id: int
    class_name: str
    bbox: Tuple[int, int, int, int]
    confidence: float
    
    # History
    positions: List[Tuple[int, int]] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    
    # State
    is_active: bool = True
    frames_tracked: int = 0
    frames_missing: int = 0
    
    # Speed
    current_speed: float = 0.0
    max_speed: float = 0.0
    avg_speed: float = 0.0
    
    # Timing
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    
    @property
    def center(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]
    
    @property
    def duration(self) -> float:
        return self.last_seen - self.first_seen
    
    @property
    def direction(self) -> Optional[str]:
        if len(self.positions) < 5:
            return None
        start = self.positions[0]
        end = self.positions[-1]
        dx, dy = end[0] - start[0], end[1] - start[1]
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        return "down" if dy > 0 else "up"
    
    def update(self, bbox: Tuple[int, int, int, int], confidence: float):
        """Update with new detection."""
        self.bbox = bbox
        self.confidence = confidence
        self.positions.append(self.center)
        self.timestamps.append(time.time())
        self.last_seen = time.time()
        self.frames_tracked += 1
        self.frames_missing = 0
        self.is_active = True
        
        # Memory management
        if len(self.positions) > 150:
            self.positions = self.positions[-150:]
            self.timestamps = self.timestamps[-150:]
    
    def mark_missing(self):
        """Mark as not detected this frame."""
        self.frames_missing += 1
    
    def get_displacement(self, n: int = 5) -> float:
        """Pixel displacement over last n positions."""
        if len(self.positions) < 2:
            return 0.0
        pts = self.positions[-n:]
        if len(pts) < 2:
            return 0.0
        dx = pts[-1][0] - pts[0][0]
        dy = pts[-1][1] - pts[0][1]
        return (dx**2 + dy**2) ** 0.5
    
    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "class_name": self.class_name,
            "bbox": self.bbox,
            "center": self.center,
            "speed": self.current_speed,
            "max_speed": self.max_speed,
            "direction": self.direction,
            "duration": round(self.duration, 1),
            "is_active": self.is_active,
        }
