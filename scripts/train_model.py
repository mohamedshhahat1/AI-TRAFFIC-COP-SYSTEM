"""
Train Custom Model Script
Fine-tune YOLOv8 on custom traffic dataset.
"""

import sys
sys.path.insert(0, '.')

try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("train_model")
except ImportError:
    from loguru import logger

try:
    from ultralytics import YOLO
except ImportError:
    logger.error("Install ultralytics: pip install ultralytics")
    sys.exit(1)


def train(
    base_model: str = "yolov8n.pt",
    data_yaml: str = "data/annotations/dataset.yaml",
    epochs: int = 100,
    img_size: int = 640,
    batch_size: int = 16,
    project: str = "models/training",
    name: str = "traffic_cop_v1",
):
    """Fine-tune YOLO model on traffic data."""
    logger.info(f"🏋️ Training: {base_model} for {epochs} epochs")
    
    model = YOLO(base_model)
    
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=img_size,
        batch=batch_size,
        project=project,
        name=name,
        patience=20,
        save=True,
        plots=True,
    )
    
    logger.info(f"✅ Training complete! Best model saved to: {project}/{name}/weights/best.pt")
    return results


if __name__ == "__main__":
    train()
