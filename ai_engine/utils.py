"""
AI Engine Utilities
Common helper functions used across all AI modules.
"""

import cv2
import numpy as np
from typing import Tuple, List
import time


def resize_frame(frame: np.ndarray, size: Tuple[int, int] = (640, 640)) -> np.ndarray:
    """Resize frame preserving aspect ratio with letterbox padding."""
    h, w = frame.shape[:2]
    tw, th = size
    scale = min(tw / w, th / h)
    nw, nh = int(w * scale), int(h * scale)
    
    resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
    padded = np.full((th, tw, 3), 114, dtype=np.uint8)
    
    x_off = (tw - nw) // 2
    y_off = (th - nh) // 2
    padded[y_off:y_off+nh, x_off:x_off+nw] = resized
    
    return padded


def enhance_frame(frame: np.ndarray) -> np.ndarray:
    """Apply CLAHE contrast enhancement."""
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def compute_iou(box1: tuple, box2: tuple) -> float:
    """Compute IoU between two bounding boxes (x1,y1,x2,y2)."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    a1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    a2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = a1 + a2 - inter
    
    return inter / union if union > 0 else 0.0


def distance(p1: tuple, p2: tuple) -> float:
    """Euclidean distance between two points."""
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5


def pixels_to_kmh(pixel_displacement: float, pixel_to_meter: float, dt: float) -> float:
    """Convert pixel displacement to km/h."""
    if dt <= 0:
        return 0.0
    meters = pixel_displacement * pixel_to_meter
    return (meters / dt) * 3.6


def draw_text_with_bg(
    frame: np.ndarray, text: str, pos: tuple,
    color: tuple = (255, 255, 255), bg_color: tuple = (0, 0, 0),
    scale: float = 0.5, thickness: int = 1,
):
    """Draw text with background rectangle."""
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    x, y = pos
    cv2.rectangle(frame, (x, y - th - 4), (x + tw, y + 4), bg_color, -1)
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)


def get_timestamp_str() -> str:
    """Get formatted timestamp string."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def create_heatmap(frame_shape: tuple, points: List[tuple], radius: int = 30) -> np.ndarray:
    """Create a heatmap from point data."""
    heatmap = np.zeros(frame_shape[:2], dtype=np.float32)
    for pt in points:
        cv2.circle(heatmap, pt, radius, 1.0, -1)
    
    heatmap = cv2.GaussianBlur(heatmap, (0, 0), radius / 2)
    heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8) if heatmap.max() > 0 else heatmap.astype(np.uint8)
    
    return cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
