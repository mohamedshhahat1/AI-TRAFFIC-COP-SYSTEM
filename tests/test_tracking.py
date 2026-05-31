"""Tests for tracking module."""

import pytest
from ai_engine.tracking.object_tracker import TrackedObject


class TestTrackedObject:
    def test_creation(self):
        t = TrackedObject(track_id=1, class_name="car", bbox=(10,20,110,120), confidence=0.85)
        assert t.track_id == 1
        assert t.center == (60, 70)
        assert t.width == 100
        assert t.height == 100
    
    def test_update(self):
        t = TrackedObject(track_id=1, class_name="car", bbox=(10,20,110,120), confidence=0.85)
        t.update((20, 30, 120, 130), 0.9)
        assert t.frames_tracked == 1
        assert t.center == (70, 80)
        assert len(t.positions) == 1
    
    def test_direction(self):
        t = TrackedObject(track_id=1, class_name="car", bbox=(100,100,200,200), confidence=0.9)
        for i in range(10):
            t.update((100+i*10, 100, 200+i*10, 200), 0.9)
        assert t.direction == "right"
