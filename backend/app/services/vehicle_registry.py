"""
Vehicle Registry Service
Backend service for plate lookup and registry management.
"""

from typing import Optional, Dict, List
from pathlib import Path

try:
    from ai_engine.plate_recognition.plate_matcher import PlateMatcher, VehicleInfo
except ImportError:
    PlateMatcher = None
    VehicleInfo = None


class VehicleRegistryService:
    """Backend service wrapping PlateMatcher for API use."""

    def __init__(self):
        if PlateMatcher:
            self.matcher = PlateMatcher()
        else:
            self.matcher = None

    def lookup(self, plate: str) -> Optional[dict]:
        if self.matcher:
            info = self.matcher.lookup(plate)
            return info.to_dict() if info else None
        return None

    def search(self, query: str) -> list:
        if self.matcher:
            return self.matcher.search(query)
        return []

    def get_all(self) -> dict:
        if self.matcher:
            return self.matcher.get_all()
        return {}

    def add_vehicle(self, plate: str, owner: str, vehicle: str, color: str):
        if self.matcher:
            self.matcher.add_vehicle(plate, owner, vehicle, color)
