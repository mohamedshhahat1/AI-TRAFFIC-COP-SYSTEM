"""Tracking module - DeepSORT Multi-Object Tracking."""
from .deep_sort_tracker import DeepSortTracker
from .object_tracker import TrackedObject

__all__ = ["DeepSortTracker", "TrackedObject"]
