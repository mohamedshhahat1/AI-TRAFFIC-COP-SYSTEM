"""
Export Model Script
Export trained model to ONNX/TensorRT for deployment.
"""

import sys
sys.path.insert(0, '.')

try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("export_model")
except ImportError:
    from loguru import logger

try:
    from ultralytics import YOLO
except ImportError:
    logger.error("Install ultralytics: pip install ultralytics")
    sys.exit(1)


def export(
    model_path: str = "models/yolov8n.pt",
    format: str = "onnx",
    img_size: int = 640,
):
    """Export model to deployment format."""
    logger.info(f"📦 Exporting {model_path} → {format}")
    
    model = YOLO(model_path)
    model.export(format=format, imgsz=img_size)
    
    logger.info(f"✅ Export complete!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/yolov8n.pt")
    parser.add_argument("--format", default="onnx", choices=["onnx", "torchscript", "engine"])
    args = parser.parse_args()
    export(args.model, args.format)
