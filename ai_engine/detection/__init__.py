"""Detection module - YOLOv8 Object Detection."""
from .yolo_detector import YOLODetector
from .model_loader import ModelLoader

__all__ = ["YOLODetector", "ModelLoader"]
