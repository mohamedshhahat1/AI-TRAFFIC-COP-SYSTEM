"""
Tests for the Object Detection module.
"""

import pytest
import numpy as np


class TestObjectDetector:
    """Test suite for ObjectDetector."""
    
    def test_detection_output_format(self):
        """Test that detections have correct format."""
        from src.vision_layer.detector import Detection
        
        det = Detection(
            bbox=(100, 100, 200, 200),
            confidence=0.85,
            class_id=2,
            class_name="car",
            center=(150, 150),
            area=10000,
        )
        
        assert det.bbox == (100, 100, 200, 200)
        assert det.confidence == 0.85
        assert det.class_name == "car"
        assert det.center == (150, 150)
        assert det.area == 10000
    
    def test_vehicle_filtering(self):
        """Test vehicle filtering from detections."""
        from src.vision_layer.detector import ObjectDetector, Detection
        
        detections = [
            Detection(bbox=(0,0,1,1), confidence=0.9, class_id=2, class_name="car", center=(0,0), area=1),
            Detection(bbox=(0,0,1,1), confidence=0.9, class_id=0, class_name="person", center=(0,0), area=1),
            Detection(bbox=(0,0,1,1), confidence=0.9, class_id=7, class_name="truck", center=(0,0), area=1),
        ]
        
        detector = ObjectDetector.__new__(ObjectDetector)
        vehicles = detector.get_vehicles(detections)
        
        assert len(vehicles) == 2
        assert all(v.class_name in ["car", "truck"] for v in vehicles)
    
    def test_pedestrian_filtering(self):
        """Test pedestrian filtering."""
        from src.vision_layer.detector import ObjectDetector, Detection
        
        detections = [
            Detection(bbox=(0,0,1,1), confidence=0.9, class_id=2, class_name="car", center=(0,0), area=1),
            Detection(bbox=(0,0,1,1), confidence=0.9, class_id=0, class_name="person", center=(0,0), area=1),
        ]
        
        detector = ObjectDetector.__new__(ObjectDetector)
        pedestrians = detector.get_pedestrians(detections)
        
        assert len(pedestrians) == 1
        assert pedestrians[0].class_name == "person"


class TestSpeedCalculator:
    """Test suite for SpeedCalculator."""
    
    def test_speed_category(self):
        """Test speed categorization."""
        from src.speed_estimation.speed_calculator import SpeedCalculator
        
        calc = SpeedCalculator(speed_limit=60)
        
        assert calc.get_speed_category(0) == "stationary"
        assert calc.get_speed_category(20) == "slow"
        assert calc.get_speed_category(50) == "normal"
        assert calc.get_speed_category(65) == "above_limit"
        assert calc.get_speed_category(80) == "speeding"
        assert calc.get_speed_category(100) == "dangerous"
    
    def test_overspeeding_detection(self):
        """Test overspeeding check."""
        from src.speed_estimation.speed_calculator import SpeedCalculator
        from src.tracking_layer.track import Track
        
        calc = SpeedCalculator(speed_limit=60)
        
        track_normal = Track(track_id=1, class_name="car", bbox=(0,0,1,1), confidence=0.9)
        track_normal.current_speed = 50
        
        track_fast = Track(track_id=2, class_name="car", bbox=(0,0,1,1), confidence=0.9)
        track_fast.current_speed = 80
        
        assert not calc.is_overspeeding(track_normal)
        assert calc.is_overspeeding(track_fast)


class TestViolation:
    """Test suite for Violation models."""
    
    def test_violation_creation(self):
        """Test violation data structure."""
        from src.violation_detection.violation import Violation, ViolationType, Severity
        
        v = Violation(
            violation_type=ViolationType.SPEED,
            severity=Severity.HIGH,
            track_id=5,
            speed=90.5,
            speed_limit=60,
        )
        
        assert v.violation_type == ViolationType.SPEED
        assert v.severity == Severity.HIGH
        assert v.speed_excess == 30.5
    
    def test_violation_serialization(self):
        """Test violation to_dict and from_dict."""
        from src.violation_detection.violation import Violation, ViolationType, Severity
        
        v = Violation(
            violation_type=ViolationType.RED_LIGHT,
            severity=Severity.CRITICAL,
            track_id=10,
            speed=45.0,
        )
        
        data = v.to_dict()
        assert data["type"] == "red_light_violation"
        assert data["severity"] == "critical"
        assert data["track_id"] == 10
        
        # Reconstruct
        v2 = Violation.from_dict(data)
        assert v2.violation_type == ViolationType.RED_LIGHT
        assert v2.track_id == 10


class TestDecisionMaker:
    """Test suite for DecisionMaker."""
    
    def test_severity_classification(self):
        """Test violation severity classification."""
        from src.decision_engine.decision_maker import DecisionMaker
        from src.violation_detection.violation import Violation, ViolationType, Severity
        
        dm = DecisionMaker()
        
        # Speed violation with 5km/h excess
        v_low = Violation(
            violation_type=ViolationType.SPEED,
            speed=65, speed_limit=60, confidence=0.9,
            bbox=(10, 10, 100, 100)
        )
        assert dm._classify_severity(v_low) == Severity.LOW
        
        # Speed violation with 25km/h excess
        v_high = Violation(
            violation_type=ViolationType.SPEED,
            speed=85, speed_limit=60, confidence=0.9,
            bbox=(10, 10, 100, 100)
        )
        assert dm._classify_severity(v_high) == Severity.HIGH
    
    def test_false_positive_filtering(self):
        """Test false positive rejection."""
        from src.decision_engine.decision_maker import DecisionMaker
        from src.violation_detection.violation import Violation, ViolationType
        
        dm = DecisionMaker()
        
        # Low confidence should be rejected
        v_low_conf = Violation(
            violation_type=ViolationType.SPEED,
            confidence=0.3,
            bbox=(10, 10, 100, 100)
        )
        assert not dm._validate_violation(v_low_conf)
        
        # Impossible speed should be rejected
        v_impossible = Violation(
            violation_type=ViolationType.SPEED,
            speed=500,
            confidence=0.9,
            bbox=(10, 10, 100, 100)
        )
        assert not dm._validate_violation(v_impossible)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
