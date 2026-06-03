"""Tests for speed estimation module."""

import pytest
from ai_engine.speed_estimation.speed_calculator import SpeedCalculator


class TestSpeedCalculator:
    def test_creation(self):
        sc = SpeedCalculator(pixel_to_meter=0.05, fps=30, speed_limit=60.0)
        assert sc.pixel_to_meter == 0.05
        assert sc.fps == 30
        assert sc.speed_limit == 60.0

    def test_from_config(self):
        config = {
            "pixel_to_meter": 0.048,
            "fps": 25,
            "speed_limit": 50.0,
        }
        sc = SpeedCalculator.from_config(config)
        assert sc.pixel_to_meter == 0.048
        assert sc.fps == 25
        assert sc.speed_limit == 50.0

    def test_from_config_with_defaults(self):
        config = {"speed_limit": 80.0}
        defaults = {"pixel_to_meter": 0.06, "fps": 30}
        sc = SpeedCalculator.from_config(config, defaults)
        assert sc.pixel_to_meter == 0.06
        assert sc.speed_limit == 80.0
        assert sc.fps == 30

    def test_update_fps(self):
        sc = SpeedCalculator()
        sc.update_fps(25)
        assert sc.fps == 25

    def test_update_fps_ignores_zero(self):
        sc = SpeedCalculator(fps=30)
        sc.update_fps(0)
        assert sc.fps == 30

    def test_is_calibrated_default(self):
        sc = SpeedCalculator()
        assert sc.is_calibrated is False

    def test_calculate_needs_min_frames(self, sample_track):
        sc = SpeedCalculator(min_track_frames=50)
        speed = sc.calculate(sample_track)
        assert speed == 0.0  # Not enough frames

    def test_calculate_with_enough_frames(self, sample_track):
        sc = SpeedCalculator(min_track_frames=5)
        speed = sc.calculate(sample_track)
        assert speed >= 0.0  # Should calculate something

    def test_is_overspeeding(self, sample_track):
        sc = SpeedCalculator(speed_limit=40.0)
        sample_track.current_speed = 55.0
        assert sc.is_overspeeding(sample_track) is True

    def test_not_overspeeding(self, sample_track):
        sc = SpeedCalculator(speed_limit=60.0)
        sample_track.current_speed = 40.0
        assert sc.is_overspeeding(sample_track) is False

    def test_get_category(self):
        sc = SpeedCalculator(speed_limit=60.0)
        assert sc.get_category(0) == "stationary"
        assert sc.get_category(20) == "slow"
        assert sc.get_category(50) == "normal"
        assert sc.get_category(65) == "above_limit"
        assert sc.get_category(80) == "speeding"
        assert sc.get_category(100) == "dangerous"

    def test_cleanup(self, sample_track):
        sc = SpeedCalculator(min_track_frames=5)
        sc.calculate(sample_track)
        assert sample_track.track_id in sc._speed_history
        sc.cleanup(sample_track.track_id)
        assert sample_track.track_id not in sc._speed_history
