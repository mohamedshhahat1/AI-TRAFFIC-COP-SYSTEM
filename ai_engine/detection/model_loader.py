"""
Model Loader Module
Handles loading, caching, and managing AI models.
"""

import os
from pathlib import Path
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("model_loader")
except ImportError:
    from loguru import logger
from typing import Optional

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None


class ModelLoader:
    """
    Manages AI model loading and caching.
    
    Supports:
    - YOLOv8 models (nano, small, medium, large, xlarge)
    - Custom trained models
    - ONNX exported models
    """
    
    AVAILABLE_MODELS = {
        "yolov8n": {"file": "yolov8n.pt", "size": "6MB", "speed": "fastest"},
        "yolov8s": {"file": "yolov8s.pt", "size": "22MB", "speed": "fast"},
        "yolov8m": {"file": "yolov8m.pt", "size": "52MB", "speed": "medium"},
        "yolov8l": {"file": "yolov8l.pt", "size": "87MB", "speed": "slow"},
        "yolov8x": {"file": "yolov8x.pt", "size": "131MB", "speed": "slowest"},
    }
    
    def __init__(self, models_dir: str = "models"):
        """Initialize model loader."""
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}
    
    def load(self, model_name: str = "yolov8n") -> Optional[object]:
        """
        Load a YOLO model by name.
        
        Args:
            model_name: Model identifier (yolov8n, yolov8s, etc.)
            
        Returns:
            Loaded YOLO model or None
        """
        if model_name in self._cache:
            logger.debug(f"Model '{model_name}' loaded from cache")
            return self._cache[model_name]
        
        if YOLO is None:
            logger.error("ultralytics not installed")
            return None
        
        model_path = self.models_dir / f"{model_name}.pt"
        
        try:
            if model_path.exists():
                model = YOLO(str(model_path))
            else:
                logger.info(f"Downloading model: {model_name}...")
                model = YOLO(f"{model_name}.pt")
            
            self._cache[model_name] = model
            logger.info(f"✅ Model loaded: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model '{model_name}': {e}")
            return None
    
    def list_available(self) -> list:
        """List available models."""
        return [
            {"name": k, **v} for k, v in self.AVAILABLE_MODELS.items()
        ]
    
    def list_downloaded(self) -> list:
        """List already downloaded models."""
        downloaded = []
        for f in self.models_dir.glob("*.pt"):
            downloaded.append(f.stem)
        return downloaded
    
    def clear_cache(self):
        """Clear model cache from memory."""
        self._cache.clear()
        logger.info("Model cache cleared")
