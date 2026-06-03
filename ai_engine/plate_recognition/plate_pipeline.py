"""
ANPR Pipeline
Orchestrates plate detection → OCR → registry lookup → evidence generation.

Integrates with Event Bus for real-time notifications.
"""

import cv2
import numpy as np
import json
import time
from typing import Optional, Dict
from dataclasses import dataclass, field
from pathlib import Path

from .plate_detector import PlateDetector, PlateDetection
from .plate_ocr import PlateOCR, OCRResult
from .plate_matcher import PlateMatcher, VehicleInfo

try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("plate_pipeline")
except (ImportError, Exception):
    from loguru import logger


@dataclass
class PlateResult:
    """Complete ANPR result for a vehicle."""
    track_id: int
    plate_detection: Optional[PlateDetection]
    ocr_result: Optional[OCRResult]
    vehicle_info: Optional[VehicleInfo]
    frame_snapshot: Optional[str] = None
    vehicle_crop_path: Optional[str] = None
    plate_crop_path: Optional[str] = None
    violation_json_path: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    @property
    def plate_number(self) -> str:
        return self.ocr_result.plate_number if self.ocr_result else ""

    @property
    def owner(self) -> str:
        return self.vehicle_info.owner if self.vehicle_info else "Unknown"

    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "plate_number": self.plate_number,
            "plate_confidence": self.ocr_result.confidence if self.ocr_result else 0,
            "owner": self.owner,
            "vehicle": self.vehicle_info.vehicle if self.vehicle_info else "Unknown",
            "color": self.vehicle_info.color if self.vehicle_info else "Unknown",
            "registered": self.vehicle_info.registered if self.vehicle_info else False,
            "timestamp": self.timestamp,
            "evidence": {
                "frame": self.frame_snapshot,
                "vehicle_crop": self.vehicle_crop_path,
                "plate_crop": self.plate_crop_path,
                "violation_json": self.violation_json_path,
            },
        }


class PlatePipeline:
    """
    Full ANPR Pipeline: Detect → Read → Match → Save Evidence.
    
    Flow:
        Vehicle bbox (from violation) 
        → Crop vehicle from frame
        → Detect plate region in crop
        → OCR read plate characters
        → Lookup in vehicle registry
        → Generate evidence package
        → Emit events
    
    Usage:
        pipeline = PlatePipeline()
        result = pipeline.process(frame, vehicle_bbox, track_id, violation_info)
        if result and result.plate_number:
            print(f"Plate: {result.plate_number} | Owner: {result.owner}")
    """

    def __init__(self, evidence_dir: str = "data/evidence"):
        self.detector = PlateDetector()
        self.ocr = PlateOCR()
        self.matcher = PlateMatcher()
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Stats
        self.total_processed = 0
        self.total_recognized = 0
        self.total_matched = 0
        
        logger.info("PlatePipeline initialized (Detect → OCR → Match → Evidence)")

    def process(
        self,
        frame: np.ndarray,
        vehicle_bbox: tuple,
        track_id: int,
        violation_info: Dict = None,
    ) -> Optional[PlateResult]:
        """
        Process a vehicle for plate recognition.
        
        Args:
            frame: Full video frame
            vehicle_bbox: (x1, y1, x2, y2) of the vehicle
            track_id: Vehicle tracking ID
            violation_info: Optional violation details
            
        Returns:
            PlateResult with all ANPR data
        """
        self.total_processed += 1
        x1, y1, x2, y2 = vehicle_bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        vehicle_crop = frame[y1:y2, x1:x2]
        if vehicle_crop.size == 0:
            return None

        # Step 1: Detect plate location
        plate_det = self.detector.detect(vehicle_crop)
        if plate_det is None:
            return PlateResult(track_id=track_id, plate_detection=None, ocr_result=None, vehicle_info=None)

        # Step 2: OCR read plate
        plate_img = plate_det.plate_image
        if plate_img is None or plate_img.size == 0:
            plate_img = vehicle_crop[plate_det.y1:plate_det.y2, plate_det.x1:plate_det.x2]

        ocr_result = self.ocr.read(plate_img)
        if ocr_result and ocr_result.plate_number:
            self.total_recognized += 1

        # Step 3: Registry lookup
        vehicle_info = None
        if ocr_result and ocr_result.plate_number:
            vehicle_info = self.matcher.lookup(ocr_result.plate_number)
            if vehicle_info and vehicle_info.registered:
                self.total_matched += 1

        # Step 4: Save evidence package
        evidence_paths = self._save_evidence(
            frame, vehicle_crop, plate_img,
            track_id, ocr_result, vehicle_info, violation_info
        )

        result = PlateResult(
            track_id=track_id,
            plate_detection=plate_det,
            ocr_result=ocr_result,
            vehicle_info=vehicle_info,
            frame_snapshot=evidence_paths.get("frame"),
            vehicle_crop_path=evidence_paths.get("vehicle"),
            plate_crop_path=evidence_paths.get("plate"),
            violation_json_path=evidence_paths.get("json"),
        )

        if ocr_result and ocr_result.plate_number:
            logger.info(
                f"Plate recognized: {ocr_result.plate_number} | "
                f"Owner: {result.owner} | Track #{track_id}"
            )

        return result

    def _save_evidence(
        self,
        frame: np.ndarray,
        vehicle_crop: np.ndarray,
        plate_img: np.ndarray,
        track_id: int,
        ocr_result: Optional[OCRResult],
        vehicle_info: Optional[VehicleInfo],
        violation_info: Optional[Dict],
    ) -> Dict[str, str]:
        """Save evidence package to disk."""
        timestamp = int(time.time() * 1000)
        evidence_id = f"{track_id}_{timestamp}"
        evidence_path = self.evidence_dir / evidence_id
        evidence_path.mkdir(parents=True, exist_ok=True)

        paths = {}

        try:
            # Save frame
            frame_path = str(evidence_path / "frame.jpg")
            cv2.imwrite(frame_path, frame)
            paths["frame"] = frame_path

            # Save vehicle crop
            vehicle_path = str(evidence_path / "vehicle_crop.jpg")
            cv2.imwrite(vehicle_path, vehicle_crop)
            paths["vehicle"] = vehicle_path

            # Save plate crop
            if plate_img is not None and plate_img.size > 0:
                plate_path = str(evidence_path / "plate_crop.jpg")
                cv2.imwrite(plate_path, plate_img)
                paths["plate"] = plate_path

            # Save violation JSON
            violation_data = {
                "plate": ocr_result.plate_number if ocr_result else "UNKNOWN",
                "plate_confidence": ocr_result.confidence if ocr_result else 0,
                "owner": vehicle_info.owner if vehicle_info else "Unknown",
                "vehicle": vehicle_info.vehicle if vehicle_info else "Unknown",
                "color": vehicle_info.color if vehicle_info else "Unknown",
                "registered": vehicle_info.registered if vehicle_info else False,
                "track_id": track_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "violation": violation_info or {},
            }
            json_path = str(evidence_path / "violation.json")
            with open(json_path, 'w') as f:
                json.dump(violation_data, f, indent=2)
            paths["json"] = json_path

        except Exception as e:
            logger.error(f"Failed to save evidence: {e}")

        return paths

    def get_stats(self) -> dict:
        return {
            "total_processed": self.total_processed,
            "total_recognized": self.total_recognized,
            "total_matched": self.total_matched,
            "recognition_rate": round(
                self.total_recognized / max(self.total_processed, 1) * 100, 1
            ),
        }
