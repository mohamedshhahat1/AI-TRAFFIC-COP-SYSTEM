"""
Automatic Number Plate Recognition (ANPR) Module
Detects, reads, and matches license plates from traffic violations.
"""

from .plate_detector import PlateDetector
from .plate_ocr import PlateOCR
from .plate_matcher import PlateMatcher
from .plate_pipeline import PlatePipeline

__all__ = ["PlateDetector", "PlateOCR", "PlateMatcher", "PlatePipeline"]
