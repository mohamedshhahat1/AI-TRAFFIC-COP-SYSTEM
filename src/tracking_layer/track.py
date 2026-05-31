"""
Track Data Structure
Represents a single tracked object with its history.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import time


@dataclass
class Track:
    """
    Represents a tracked vehicle/object with its movement history.
    """
    track_id: int
    class_name: str
    bbox: Tuple[int, int, int, int]  # Current bounding box (x1, y1, x2, y2)
    confidence: float
    
    # Movement history
    positions: List[Tuple[int, int]] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    
    # State
    is_active: bool = True
    frames_since_update: int = 0
    total_frames: int = 0
    
    # Speed info
    current_speed: float = 0.0
    max_speed: float = 0.0
    avg_speed: float = 0.0
    
    # First and last seen
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get current center position."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    @property
    def width(self) -> int:
        """Get bounding box width."""
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> int:
        """Get bounding box height."""
        return self.bbox[3] - self.bbox[1]
    
    @property
    def area(self) -> int:
        """Get bounding box area."""
        return self.width * self.height
    
    @property
    def duration(self) -> float:
        """Get tracking duration in seconds."""
        return self.last_seen - self.first_seen
    
    @property
    def direction(self) -> Optional[str]:
        """Estimate movement direction based on position history."""
        if len(self.positions) < 2:
            return None
        
        start = self.positions[0]
        end = self.positions[-1]
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"
    
    def update(self, bbox: Tuple[int, int, int, int], confidence: float):
        """Update track with new detection."""
        self.bbox = bbox
        self.confidence = confidence
        self.positions.append(self.center)
        self.timestamps.append(time.time())
        self.last_seen = time.time()
        self.frames_since_update = 0
        self.total_frames += 1
        self.is_active = True
        
        # Keep only last 100 positions for memory efficiency
        if len(self.positions) > 100:
            self.positions = self.positions[-100:]
            self.timestamps = self.timestamps[-100:]
    
    def mark_missed(self):
        """Mark track as missed (no detection this frame)."""
        self.frames_since_update += 1
    
    def get_displacement(self, n_frames: int = 5) -> float:
        """
        Get pixel displacement over last n frames.
        
        Args:
            n_frames: Number of frames to calculate displacement over
            
        Returns:
            Pixel displacement
        """
        if len(self.positions) < 2:
            return 0.0
        
        positions = self.positions[-n_frames:]
        if len(positions) < 2:
            return 0.0
        
        start = positions[0]
        end = positions[-1]
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        return (dx**2 + dy**2) ** 0.5
    
    def to_dict(self) -> dict:
        """Convert track to dictionary."""
        return {
            "track_id": self.track_id,
            "class_name": self.class_name,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "center": self.center,
            "current_speed": self.current_speed,
            "max_speed": self.max_speed,
            "direction": self.direction,
            "duration": self.duration,
            "is_active": self.is_active,
            "total_frames": self.total_frames,
        }
