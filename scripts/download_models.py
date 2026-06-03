#!/usr/bin/env python3
"""
Download Model Weights Script
Downloads pre-trained YOLOv8 model weights for the AI Traffic Cop System.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, '.')

try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("download_models")
except ImportError:
    from loguru import logger


# Available models (smallest → largest)
MODELS = {
    "yolov8n": {
        "description": "YOLOv8 Nano - Fastest, lowest accuracy (recommended for CPU)",
        "size_mb": 6,
    },
    "yolov8s": {
        "description": "YOLOv8 Small - Good balance of speed and accuracy",
        "size_mb": 22,
    },
    "yolov8m": {
        "description": "YOLOv8 Medium - Higher accuracy, moderate speed",
        "size_mb": 50,
    },
    "yolov8l": {
        "description": "YOLOv8 Large - High accuracy, GPU recommended",
        "size_mb": 84,
    },
}


def download_model(model_name: str = "yolov8n", output_dir: str = "models"):
    """
    Download YOLOv8 model weights from Ultralytics.

    Args:
        model_name: Model variant (yolov8n, yolov8s, yolov8m, yolov8l)
        output_dir: Directory to save model weights
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    model_file = f"{model_name}.pt"
    target_path = output_path / model_file

    if target_path.exists():
        logger.info(f"✅ Model already exists: {target_path}")
        return str(target_path)

    logger.info(f"⬇️  Downloading {model_name} ({MODELS.get(model_name, {}).get('size_mb', '?')}MB)...")
    logger.info(f"   {MODELS.get(model_name, {}).get('description', '')}")

    # YOLO() auto-downloads the model if not present
    model = YOLO(model_name + ".pt")

    # Move to our models directory
    src_path = Path(model_name + ".pt")
    if src_path.exists() and str(src_path.resolve()) != str(target_path.resolve()):
        src_path.rename(target_path)
        logger.info(f"✅ Model saved to: {target_path}")
    elif target_path.exists():
        logger.info(f"✅ Model available at: {target_path}")
    else:
        logger.warning(f"⚠️  Model downloaded but may be in ultralytics cache")

    return str(target_path)


def verify_model(model_path: str):
    """Verify model loads correctly."""
    try:
        from ultralytics import YOLO
        model = YOLO(model_path)
        logger.info(f"✅ Model verified: {model_path}")
        logger.info(f"   Classes: {len(model.names)} ({', '.join(list(model.names.values())[:5])}...)")
        return True
    except Exception as e:
        logger.error(f"❌ Model verification failed: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download YOLOv8 model weights")
    parser.add_argument(
        "--model", "-m",
        default="yolov8n",
        choices=list(MODELS.keys()),
        help="Model variant to download (default: yolov8n)"
    )
    parser.add_argument(
        "--output", "-o",
        default="models",
        help="Output directory (default: models/)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all model variants"
    )

    args = parser.parse_args()

    print("\n🚔 AI Traffic Cop System - Model Downloader\n")
    print("Available models:")
    for name, info in MODELS.items():
        print(f"  {name:10s} - {info['description']} (~{info['size_mb']}MB)")
    print()

    if args.all:
        for model_name in MODELS:
            path = download_model(model_name, args.output)
            verify_model(path)
    else:
        path = download_model(args.model, args.output)
        verify_model(path)

    print("\n✅ Done! Models are ready for inference.")
    print("   Start the system with: python -m uvicorn backend.app.main:app --reload")
