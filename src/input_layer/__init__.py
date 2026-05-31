"""
Input Layer Module - Camera Feed & Video Source Management
Handles RTSP streams, video files, and live camera connections.
"""

from .camera_feed import CameraFeed
from .frame_processor import FrameProcessor

__all__ = ["CameraFeed", "FrameProcessor"]
