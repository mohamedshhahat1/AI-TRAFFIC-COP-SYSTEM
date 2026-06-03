"""Tests for violation detection modules."""

import pytest
import time
from ai_engine.violation_detection.lane_violation import LaneViolationDetector
from ai_engine.violation_detection.red_light import RedLightDetector


class TestLaneViolationDetector:
    def test_creation_default(self):
        det = LaneViolationDetector()
        assert len(det.lane_boundaries) == 4

    def test_creation_custom_boundaries(self):
        det = LaneViolationDetector(lane_boundaries=[100, 300, 500])
        assert det.lane_boundaries == [100, 300, 500]

    def test_from_config(self):
        config = {"lane_boundaries": [150, 350, 550], "frame_width": 800}
        det = LaneViolationDetector.from_config(config)
        assert det.lane_boundaries == [150, 350, 550]

    def test_from_config_auto_boundaries(self):
        config = {"frame_width": 1000}
        det = LaneViolationDetector.from_config(config)
        assert len(det.lane_boundaries) == 4
        # Evenly spaced: 200, 400, 600, 800
        assert det.lane_boundaries == [200, 400, 600, 800]

    def test_no_violation_short_track(self, sample_track):
        det = LaneViolationDetector()
        sample_track.positions = [(100, 100)] * 5  # Too few
        result = det.check(sample_track)
        assert result is None


class TestRedLightDetector:
    def test_creation(self):
        det = RedLightDetector(stop_line_y=400)
        assert det.stop_line_y == 400
        assert det.traffic_light_state == "unknown"

    def test_set_light_state(self):
        det = RedLightDetector()
        det.set_light_state("red")
        assert det.traffic_light_state == "red"

    def test_no_violation_when_green(self, sample_track):
        det = RedLightDetector()
        det.set_light_state("green")
        result = det.check(sample_track)
        assert result is None

    def test_no_violation_when_unknown(self, sample_track):
        det = RedLightDetector()
        result = det.check(sample_track)
        assert result is None

    def test_violation_crossing_red(self, sample_track):
        det = RedLightDetector(stop_line_y=275)
        det.set_light_state("red")
        # Position just before and after stop line
        sample_track.positions = [(175, 270), (175, 280)]
        sample_track.current_speed = 60.0
        result = det.check(sample_track)
        assert result is not None
        assert result.severity == "critical"  # speed > 50

    def test_cooldown_prevents_duplicate(self, sample_track):
        det = RedLightDetector(stop_line_y=275)
        det.set_light_state("red")
        sample_track.positions = [(175, 270), (175, 280)]
        sample_track.current_speed = 60.0

        # First detection
        result1 = det.check(sample_track)
        assert result1 is not None

        # Second check within cooldown
        sample_track.positions = [(175, 270), (175, 280)]
        result2 = det.check(sample_track)
        assert result2 is None  # In cooldown
