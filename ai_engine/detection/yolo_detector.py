"""
YOLO Detector Module
Real-time object detection using YOLOv8 for traffic monitoring.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from loguru import logger

from .model_loader import ModelLoader


@dataclass
class Detection:
    """Single detection result."""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str
    center: Tuple[int, int]
    area: int


class YOLODetector:
    """
    YOLOv8-based detector optimized for traffic objects.
    
    Detects: Cars, Trucks, Buses, Motorcycles, Bicycles,
    Pedestrians, Traffic Lights, Stop Signs
    """
    
    # COCO classes relevant to traffic
    TRAFFIC_CLASSES = {
        0: "person", 1: "bicycle", 2: "car", 3: "motorcycle",
        5: "bus", 7: "truck", 9: "traffic_light", 11: "stop_sign",
    }
    
    COLORS = {
        "person": (0, 255, 0), "bicycle": (255, 255, 0),
        "car": (0, 165, 255), "motorcycle": (0, 255, 255),
        "bus": (255, 0, 255), "truck": (255, 0, 0),
        "traffic_light": (0, 0, 255), "stop_sign": (128, 0, 128),
    }
    
    def __init__(
        self,
        model_name: str = "yolov8n",
        confidence: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = "auto",
        img_size: int = 640,
    ):
        """
        Initialize YOLO detector.
        
        Args:
            model_name: YOLO model variant
            confidence: Minimum confidence threshold
            iou_threshold: Non-max suppression IoU threshold
            device: Inference device (auto/cpu/cuda:0)
            img_size: Input image size
        """
        self.confidence = confidence
        self.iou_threshold = iou_threshold
        self.img_size = img_size
        self.device = device
        
        # Load model
        loader = ModelLoader()
        self.model = loader.load(model_name)
        
        # Resolve device
        if self.device == "auto":
            try:
                import torch
                self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"
        
        logger.info(f"YOLODetector ready | device={self.device} | conf={confidence}")
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run detection on a single frame.
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            List of Detection objects
        """
        if self.model is None:
            return []
        
        detections = []
        
        try:
            results = self.model(
                frame,
                conf=self.confidence,
                iou=self.iou_threshold,
                device=self.device,
                imgsz=self.img_size,
                verbose=False,
                classes=list(self.TRAFFIC_CLASSES.keys()),
            )
            
            for result in results:
                if result.boxes is None:
                    continue
                
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    cls_name = self.TRAFFIC_CLASSES.get(cls_id, "unknown")
                    
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    area = (x2 - x1) * (y2 - y1)
                    
                    detections.append(Detection(
                        bbox=(x1, y1, x2, y2),
                        confidence=conf,
                        class_id=cls_id,
                        class_name=cls_name,
                        center=(cx, cy),
                        area=area,
                    ))
        
        except Exception as e:
            logger.error(f"Detection failed: {e}")
        
        return detections
    
    def detect_and_annotate(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Detection]]:
        """Detect and draw bounding boxes on frame."""
        detections = self.detect(frame)
        annotated = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = self.COLORS.get(det.class_name, (255, 255, 255))
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            label = f"{det.class_name} {det.confidence:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw, y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 4),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated, detections
    
    def filter_vehicles(self, detections: List[Detection]) -> List[Detection]:
        """Get only vehicle detections."""
        vehicles = {"car", "truck", "bus", "motorcycle", "bicycle"}
        return [d for d in detections if d.class_name in vehicles]
    
    def filter_pedestrians(self, detections: List[Detection]) -> List[Detection]:
        """Get only pedestrian detections."""
        return [d for d in detections if d.class_name == "person"]
    
    def filter_traffic_lights(self, detections: List[Detection]) -> List[Detection]:
        """Get only traffic light detections."""
        return [d for d in detections if d.class_name == "traffic_light"]
    
    def count_by_class(self, detections: List[Detection]) -> Dict[str, int]:
        """Count objects per class."""
        counts = {}
        for d in detections:
            counts[d.class_name] = counts.get(d.class_name, 0) + 1
        return counts
