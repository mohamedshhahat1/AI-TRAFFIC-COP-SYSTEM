"""
Model Download Utility
Downloads YOLOv8 pre-trained models for traffic detection.
"""

import os
from pathlib import Path
from loguru import logger

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None


def download_yolo_model(
    model_name: str = "yolov8n.pt",
    save_dir: str = "models"
) -> str:
    """
    Download YOLOv8 model weights.
    
    Available models:
    - yolov8n.pt (Nano - fastest, least accurate)
    - yolov8s.pt (Small - balanced)
    - yolov8m.pt (Medium - good accuracy)
    - yolov8l.pt (Large - high accuracy)
    - yolov8x.pt (Extra Large - best accuracy, slowest)
    
    Args:
        model_name: Name of the YOLO model to download
        save_dir: Directory to save the model
        
    Returns:
        Path to the downloaded model
    """
    if YOLO is None:
        logger.error("ultralytics package not installed")
        return ""
    
    # Create save directory
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    
    model_path = save_path / model_name
    
    if model_path.exists():
        logger.info(f"Model already exists: {model_path}")
        return str(model_path)
    
    try:
        logger.info(f"Downloading {model_name}...")
        
        # Loading YOLO with a model name triggers download
        model = YOLO(model_name)
        
        # Move to save directory
        import shutil
        default_path = Path(model_name)
        if default_path.exists():
            shutil.move(str(default_path), str(model_path))
        
        logger.info(f"Model downloaded successfully: {model_path}")
        return str(model_path)
        
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return ""


def list_available_models() -> list:
    """List available YOLOv8 models."""
    return [
        {"name": "yolov8n.pt", "size": "~6MB", "speed": "fastest", "accuracy": "basic"},
        {"name": "yolov8s.pt", "size": "~22MB", "speed": "fast", "accuracy": "good"},
        {"name": "yolov8m.pt", "size": "~52MB", "speed": "medium", "accuracy": "better"},
        {"name": "yolov8l.pt", "size": "~87MB", "speed": "slow", "accuracy": "high"},
        {"name": "yolov8x.pt", "size": "~131MB", "speed": "slowest", "accuracy": "best"},
    ]


if __name__ == "__main__":
    print("Available YOLOv8 Models:")
    print("-" * 60)
    for model in list_available_models():
        print(f"  {model['name']:15} | Size: {model['size']:8} | "
              f"Speed: {model['speed']:8} | Accuracy: {model['accuracy']}")
    print("-" * 60)
    
    # Download default model
    path = download_yolo_model("yolov8n.pt")
    if path:
        print(f"\n✅ Model ready at: {path}")
