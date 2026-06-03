"""Shared test fixtures."""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_violation():
    """Sample violation data for testing."""
    return {
        "type": "speed_violation",
        "severity": "high",
        "track_id": 42,
        "vehicle_class": "car",
        "speed": 85.5,
        "speed_limit": 60.0,
        "description": "Vehicle exceeding speed limit by 25.5 km/h",
    }


@pytest.fixture
def sample_track():
    """Mock tracked object for testing."""
    class MockTrack:
        def __init__(self):
            self.track_id = 1
            self.class_name = "car"
            self.bbox = (100, 200, 250, 350)
            self.center = (175, 275)
            self.current_speed = 45.0
            self.max_speed = 65.0
            self.avg_speed = 42.0
            self.positions = [(170 + i, 270 + i) for i in range(20)]
            self.timestamps = [i * 0.033 for i in range(20)]
            self.frames_tracked = 20

    return MockTrack()
