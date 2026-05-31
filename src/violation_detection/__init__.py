"""
Violation Detection Engine
Detects traffic violations: speed, red light, lane, parking.
"""

from .violation_detector import ViolationDetector
from .violation import Violation, ViolationType, Severity

__all__ = ["ViolationDetector", "Violation", "ViolationType", "Severity"]
