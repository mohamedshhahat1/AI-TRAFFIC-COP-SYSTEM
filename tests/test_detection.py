"""Tests for object detection module."""

import pytest
import numpy as np
from ai_engine.detection.yolo_detector import Detection, YOLODetector


class TestDetection:
    def test_detection_dataclass(self):
        det = Detection(
            bbox=(100, 100, 200, 200), confidence=0.9,
            class_id=2, class_name="car", center=(150, 150), area=10000
        )
        assert det.class_name == "car"
        assert det.confidence == 0.9
        assert det.center == (150, 150)
    
    def test_vehicle_filter(self):
        dets = [
            Detection((0,0,1,1), 0.9, 2, "car", (0,0), 1),
            Detection((0,0,1,1), 0.9, 0, "person", (0,0), 1),
            Detection((0,0,1,1), 0.9, 7, "truck", (0,0), 1),
        ]
        detector = YOLODetector.__new__(YOLODetector)
        vehicles = detector.filter_vehicles(dets)
        assert len(vehicles) == 2

    def test_count_by_class(self):
        dets = [
            Detection((0,0,1,1), 0.9, 2, "car", (0,0), 1),
            Detection((0,0,1,1), 0.9, 2, "car", (0,0), 1),
            Detection((0,0,1,1), 0.9, 7, "truck", (0,0), 1),
        ]
        detector = YOLODetector.__new__(YOLODetector)
        counts = detector.count_by_class(dets)
        assert counts["car"] == 2
        assert counts["truck"] == 1
