"""
Object Detector Module
YOLOv8-based real-time object detection for traffic monitoring.
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

try:
    from ultralytics import YOLO
except ImportError:
    logger.warning("ultralytics not installed. Run: pip install ultralytics")
    YOLO = None


@dataclass
class Detection:
    """Represents a single object detection."""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str
    center: Tuple[int, int]
    area: int


class ObjectDetector:
    """
    YOLOv8 Object Detector for traffic monitoring.
    
    Detects:
    - Cars, trucks, buses, motorcycles
    - Pedestrians
    - Traffic lights
    """
    
    # COCO class IDs relevant to traffic
    TRAFFIC_CLASSES = {
        0: "person",
        1: "bicycle",
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck",
        9: "traffic light",
        11: "stop sign",
    }
    
    # Colors for visualization (BGR)
    CLASS_COLORS = {
        "person": (0, 255, 0),
        "bicycle": (255, 255, 0),
        "car": (0, 165, 255),
        "motorcycle": (0, 255, 255),
        "bus": (255, 0, 255),
        "truck": (255, 0, 0),
        "traffic light": (0, 0, 255),
        "stop sign": (128, 0, 128),
    }
    
    def __init__(
        self,
        model_path: str = "models/yolov8n.pt",
        confidence: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = "auto",
        img_size: int = 640
    ):
        """
        Initialize the object detector.
        
        Args:
            model_path: Path to YOLOv8 model weights
            confidence: Minimum detection confidence threshold
            iou_threshold: IoU threshold for NMS
            device: Device to run inference (auto, cpu, cuda:0)
            img_size: Input image size for the model
        """
        self.model_path = model_path
        self.confidence = confidence
        self.iou_threshold = iou_threshold
        self.device = device
        self.img_size = img_size
        self.model = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the YOLOv8 model."""
        if YOLO is None:
            logger.error("ultralytics package not available")
            return
        
        try:
            self.model = YOLO(self.model_path)
            
            # Set device
            if self.device == "auto":
                import torch
                self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
            
            logger.info(f"YOLOv8 model loaded: {self.model_path} on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run object detection on a frame.
        
        Args:
            frame: Input BGR frame
            
        Returns:
            List of Detection objects
        """
        if self.model is None:
            logger.warning("Model not loaded, skipping detection")
            return []
        
        detections = []
        
        try:
            # Run inference
            results = self.model(
                frame,
                conf=self.confidence,
                iou=self.iou_threshold,
                device=self.device,
                imgsz=self.img_size,
                verbose=False,
                classes=list(self.TRAFFIC_CLASSES.keys())
            )
            
            # Parse results
            for result in results:
                boxes = result.boxes
                
                if boxes is None:
                    continue
                
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    
                    # Get confidence and class
                    conf = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.TRAFFIC_CLASSES.get(class_id, "unknown")
                    
                    # Calculate center and area
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    area = (x2 - x1) * (y2 - y1)
                    
                    detection = Detection(
                        bbox=(x1, y1, x2, y2),
                        confidence=conf,
                        class_id=class_id,
                        class_name=class_name,
                        center=(center_x, center_y),
                        area=area
                    )
                    detections.append(detection)
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
        
        return detections
    
    def detect_and_draw(
        self, 
        frame: np.ndarray, 
        draw_labels: bool = True,
        draw_confidence: bool = True
    ) -> Tuple[np.ndarray, List[Detection]]:
        """
        Detect objects and draw bounding boxes on the frame.
        
        Args:
            frame: Input BGR frame
            draw_labels: Whether to draw class labels
            draw_confidence: Whether to draw confidence scores
            
        Returns:
            Tuple of (annotated frame, list of detections)
        """
        detections = self.detect(frame)
        annotated = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = self.CLASS_COLORS.get(det.class_name, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            if draw_labels:
                label = det.class_name
                if draw_confidence:
                    label += f" {det.confidence:.2f}"
                
                # Background for text
                (text_w, text_h), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
                )
                cv2.rectangle(
                    annotated, 
                    (x1, y1 - text_h - 10), 
                    (x1 + text_w, y1), 
                    color, -1
                )
                cv2.putText(
                    annotated, label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 1
                )
        
        return annotated, detections
    
    def get_vehicles(self, detections: List[Detection]) -> List[Detection]:
        """Filter detections to only vehicles."""
        vehicle_classes = {"car", "truck", "bus", "motorcycle", "bicycle"}
        return [d for d in detections if d.class_name in vehicle_classes]
    
    def get_pedestrians(self, detections: List[Detection]) -> List[Detection]:
        """Filter detections to only pedestrians."""
        return [d for d in detections if d.class_name == "person"]
    
    def get_traffic_lights(self, detections: List[Detection]) -> List[Detection]:
        """Filter detections to only traffic lights."""
        return [d for d in detections if d.class_name == "traffic light"]
    
    def count_by_class(self, detections: List[Detection]) -> Dict[str, int]:
        """Count detections by class."""
        counts = {}
        for det in detections:
            counts[det.class_name] = counts.get(det.class_name, 0) + 1
        return counts
    
    def set_confidence(self, confidence: float):
        """Update confidence threshold."""
        self.confidence = max(0.0, min(1.0, confidence))
        logger.info(f"Confidence threshold updated to: {self.confidence}")
    
    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "model_path": self.model_path,
            "device": self.device,
            "confidence": self.confidence,
            "iou_threshold": self.iou_threshold,
            "img_size": self.img_size,
            "loaded": self.model is not None,
            "classes": list(self.TRAFFIC_CLASSES.values()),
        }
