"""
License Plate Detector
Detects the bounding box of license plates within a vehicle crop.

Technology: YOLOv8 (plate detection model) + OpenCV fallback
Input: Vehicle image crop (from main detector's bounding box)
Output: Plate bounding box coordinates + confidence
"""

import cv2
import numpy as np
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass
from pathlib import Path

try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("plate_detector")
except (ImportError, Exception):
    from loguru import logger


@dataclass
class PlateDetection:
    """Detected license plate location."""
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    plate_image: Optional[np.ndarray] = None

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def center(self) -> Tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def to_dict(self) -> dict:
        return {
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2,
            "confidence": round(self.confidence, 2),
            "width": self.width,
            "height": self.height,
        }


class PlateDetector:
    """
    Detects license plates within vehicle bounding boxes.
    
    Strategy:
    1. Try YOLOv8 plate model (if available)
    2. Fallback to OpenCV contour detection
    
    Usage:
        detector = PlateDetector()
        plate = detector.detect(vehicle_crop)
        if plate:
            print(f"Plate at {plate.x1},{plate.y1} conf={plate.confidence}")
    """

    def __init__(self, model_path: str = "models/plate_detector.pt"):
        """
        Initialize plate detector.
        
        Args:
            model_path: Path to YOLOv8 plate detection model (optional)
        """
        self.model = None
        self.model_path = model_path
        self._load_model()
        logger.info("PlateDetector initialized")

    def _load_model(self):
        """Try to load YOLOv8 plate detection model."""
        try:
            from ultralytics import YOLO
            model_file = Path(self.model_path)
            if model_file.exists():
                self.model = YOLO(str(model_file))
                logger.info(f"Plate YOLO model loaded: {self.model_path}")
            else:
                logger.info("No plate model found — using OpenCV fallback")
        except Exception as e:
            logger.warning(f"Could not load plate model: {e}")

    def detect(self, vehicle_crop: np.ndarray) -> Optional[PlateDetection]:
        """
        Detect license plate in a vehicle image crop.
        
        Args:
            vehicle_crop: BGR image of the vehicle (cropped from main frame)
            
        Returns:
            PlateDetection if found, None otherwise
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return None

        # Try YOLO model first
        if self.model is not None:
            result = self._detect_yolo(vehicle_crop)
            if result:
                return result

        # Fallback: OpenCV-based detection
        return self._detect_opencv(vehicle_crop)

    def _detect_yolo(self, crop: np.ndarray) -> Optional[PlateDetection]:
        """Detect plate using YOLOv8 model."""
        try:
            results = self.model(crop, conf=0.3, verbose=False)
            if results[0].boxes is not None and len(results[0].boxes) > 0:
                box = results[0].boxes[0]  # Best detection
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                plate_img = crop[y1:y2, x1:x2]
                return PlateDetection(x1=x1, y1=y1, x2=x2, y2=y2,
                                     confidence=conf, plate_image=plate_img)
        except Exception as e:
            logger.error(f"YOLO plate detection error: {e}")
        return None

    def _detect_opencv(self, crop: np.ndarray) -> Optional[PlateDetection]:
        """
        Detect plate using OpenCV contour analysis.
        Looks for rectangular regions with plate-like aspect ratio.
        """
        h, w = crop.shape[:2]
        if h < 20 or w < 20:
            return None

        # Convert to grayscale
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        # Apply bilateral filter to reduce noise
        gray = cv2.bilateralFilter(gray, 11, 17, 17)

        # Edge detection
        edges = cv2.Canny(gray, 30, 200)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours for plate-like rectangles
        candidates = []
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:  # Rectangle
                x, y, cw, ch = cv2.boundingRect(approx)
                aspect_ratio = cw / max(ch, 1)
                area = cw * ch
                # Plate aspect ratio: typically 2:1 to 5:1
                if 2.0 < aspect_ratio < 6.0 and area > (w * h * 0.01):
                    candidates.append((x, y, x + cw, y + ch, area))

        if not candidates:
            # Fallback: look in bottom third of vehicle (common plate location)
            plate_region_y = int(h * 0.6)
            plate_region = crop[plate_region_y:, :]
            if plate_region.size > 0:
                ph, pw = plate_region.shape[:2]
                # Estimate plate in center-bottom
                px1 = int(pw * 0.2)
                py1 = plate_region_y + int(ph * 0.3)
                px2 = int(pw * 0.8)
                py2 = plate_region_y + int(ph * 0.9)
                plate_img = crop[py1:py2, px1:px2]
                if plate_img.size > 0:
                    return PlateDetection(x1=px1, y1=py1, x2=px2, y2=py2,
                                         confidence=0.4, plate_image=plate_img)
            return None

        # Take largest candidate
        candidates.sort(key=lambda c: c[4], reverse=True)
        x1, y1, x2, y2, _ = candidates[0]
        plate_img = crop[y1:y2, x1:x2]

        return PlateDetection(x1=x1, y1=y1, x2=x2, y2=y2,
                             confidence=0.7, plate_image=plate_img)

    def detect_from_frame(self, frame: np.ndarray, vehicle_bbox: Tuple[int, int, int, int]) -> Optional[PlateDetection]:
        """
        Detect plate from full frame given vehicle bounding box.
        
        Args:
            frame: Full video frame
            vehicle_bbox: (x1, y1, x2, y2) of the vehicle
        """
        x1, y1, x2, y2 = vehicle_bbox
        # Clamp
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        vehicle_crop = frame[y1:y2, x1:x2]
        plate = self.detect(vehicle_crop)

        if plate:
            # Convert coordinates to full frame
            plate.x1 += x1
            plate.y1 += y1
            plate.x2 += x1
            plate.y2 += y1

        return plate
