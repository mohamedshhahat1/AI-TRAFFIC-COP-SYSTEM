"""
Tracking Layer Module - DeepSORT Vehicle Tracking
Assigns unique IDs and tracks vehicles across frames.
"""

from .tracker import VehicleTracker
from .track import Track

__all__ = ["VehicleTracker", "Track"]
