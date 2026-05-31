"""
AI Vision Layer Module - YOLOv8 Object Detection
Detects vehicles, pedestrians, and traffic lights in real-time.
"""

from .detector import ObjectDetector
from .download_model import download_yolo_model

__all__ = ["ObjectDetector", "download_yolo_model"]
