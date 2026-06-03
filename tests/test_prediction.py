"""Tests for accident prediction module."""

import pytest
from ai_engine.prediction.accident_predictor import AccidentPredictor, AccidentRisk


class TestAccidentPredictor:
    def test_creation(self):
        ap = AccidentPredictor()
        assert ap.min_ttc_warning == 1.0
        assert ap.min_ttc_critical == 0.3
        assert ap.fps == 30

    def test_creation_custom_fps(self):
        ap = AccidentPredictor(fps=25)
        assert ap.fps == 25

    def test_update_fps(self):
        ap = AccidentPredictor(fps=30)
        ap.update_fps(25)
        assert ap.fps == 25

    def test_no_risk_single_vehicle(self, sample_track):
        ap = AccidentPredictor()
        risks = ap.analyze([sample_track])
        assert len(risks) == 0  # Need at least 2 vehicles

    def test_no_risk_far_apart(self, sample_track):
        """Two vehicles far apart should not trigger risk."""
        class FarTrack:
            def __init__(self):
                self.track_id = 2
                self.class_name = "car"
                self.bbox = (800, 800, 900, 900)
                self.center = (850, 850)
                self.current_speed = 30.0
                self.positions = [(800 + i, 800 + i) for i in range(20)]
                self.timestamps = [i * 0.033 for i in range(20)]
                self.frames_tracked = 20

        ap = AccidentPredictor(proximity_threshold=30)
        risks = ap.analyze([sample_track, FarTrack()])
        # They are >600px apart, should not trigger
        assert len(risks) == 0

    def test_get_stats(self):
        ap = AccidentPredictor()
        stats = ap.get_stats()
        assert "total_risks_detected" in stats
        assert "current_active" in stats
        assert "imminent_risks" in stats

    def test_get_current_risks_empty(self):
        ap = AccidentPredictor()
        risks = ap.get_current_risks("medium")
        assert len(risks) == 0
