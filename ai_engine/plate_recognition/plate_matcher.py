"""
Plate Matcher Module
Matches detected plate numbers with vehicle registry database.

Input: Plate number string
Output: Vehicle owner info + history
"""

import json
from typing import Optional, Dict
from dataclasses import dataclass
from pathlib import Path

try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("plate_matcher")
except (ImportError, Exception):
    from loguru import logger


@dataclass
class VehicleInfo:
    """Vehicle information from registry."""
    plate_number: str
    owner: str
    vehicle: str
    color: str
    registered: bool = True
    violations_history: int = 0

    def to_dict(self) -> dict:
        return {
            "plate_number": self.plate_number,
            "owner": self.owner,
            "vehicle": self.vehicle,
            "color": self.color,
            "registered": self.registered,
            "violations_history": self.violations_history,
        }


class PlateMatcher:
    """
    Matches license plates against vehicle registry.
    
    Registry sources:
    1. Local JSON file (data/vehicle_registry/registry.json)
    2. In-memory cache for fast lookups
    3. Extensible for external API/database integration
    
    Usage:
        matcher = PlateMatcher()
        info = matcher.lookup("ABC1234")
        if info:
            print(f"Owner: {info.owner}, Vehicle: {info.vehicle}")
    """

    def __init__(self, registry_path: str = "data/vehicle_registry/registry.json"):
        """
        Initialize plate matcher with registry file.
        
        Args:
            registry_path: Path to vehicle registry JSON
        """
        self.registry_path = Path(registry_path)
        self._registry: Dict[str, dict] = {}
        self._load_registry()
        logger.info(f"PlateMatcher initialized | {len(self._registry)} vehicles in registry")

    def _load_registry(self):
        """Load vehicle registry from JSON file."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path) as f:
                    self._registry = json.load(f)
                logger.info(f"Registry loaded: {len(self._registry)} entries")
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                self._registry = {}
        else:
            # Create default sample registry
            self._registry = self._create_sample_registry()
            self._save_registry()

    def _create_sample_registry(self) -> Dict[str, dict]:
        """Create a sample vehicle registry for demo."""
        return {
            "ABC1234": {"owner": "Ahmed Mohamed", "vehicle": "Toyota Corolla 2022", "color": "White", "violations_history": 2},
            "XYZ5678": {"owner": "Mohamed Ali", "vehicle": "Hyundai Elantra 2021", "color": "Silver", "violations_history": 0},
            "DEF9012": {"owner": "Sara Hassan", "vehicle": "Kia Sportage 2023", "color": "Black", "violations_history": 1},
            "GHI3456": {"owner": "Omar Khaled", "vehicle": "Nissan Sunny 2020", "color": "Red", "violations_history": 5},
            "JKL7890": {"owner": "Fatma Ibrahim", "vehicle": "Toyota Yaris 2022", "color": "Blue", "violations_history": 0},
            "MNO2345": {"owner": "Hassan Ahmed", "vehicle": "Chevrolet Optra 2019", "color": "Gray", "violations_history": 3},
            "PQR6789": {"owner": "Nour Saeed", "vehicle": "Hyundai Accent 2021", "color": "White", "violations_history": 1},
            "STU0123": {"owner": "Youssef Tarek", "vehicle": "Suzuki Swift 2020", "color": "Green", "violations_history": 0},
        }

    def _save_registry(self):
        """Save registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(self._registry, f, indent=2)
        logger.info(f"Registry saved: {len(self._registry)} entries")

    def lookup(self, plate_number: str) -> Optional[VehicleInfo]:
        """
        Look up a plate number in the registry.
        
        Args:
            plate_number: Cleaned plate string (e.g., "ABC1234")
            
        Returns:
            VehicleInfo if found, None if unregistered
        """
        plate = plate_number.upper().strip()

        if plate in self._registry:
            entry = self._registry[plate]
            return VehicleInfo(
                plate_number=plate,
                owner=entry.get("owner", "Unknown"),
                vehicle=entry.get("vehicle", "Unknown"),
                color=entry.get("color", "Unknown"),
                registered=True,
                violations_history=entry.get("violations_history", 0),
            )

        # Not in registry
        return VehicleInfo(
            plate_number=plate,
            owner="Unregistered",
            vehicle="Unknown",
            color="Unknown",
            registered=False,
            violations_history=0,
        )

    def add_vehicle(self, plate: str, owner: str, vehicle: str, color: str):
        """Add a vehicle to the registry."""
        self._registry[plate.upper()] = {
            "owner": owner,
            "vehicle": vehicle,
            "color": color,
            "violations_history": 0,
        }
        self._save_registry()

    def increment_violations(self, plate: str):
        """Increment violation count for a plate."""
        plate = plate.upper()
        if plate in self._registry:
            self._registry[plate]["violations_history"] = \
                self._registry[plate].get("violations_history", 0) + 1
            self._save_registry()

    def get_all(self) -> Dict[str, dict]:
        """Get full registry."""
        return self._registry

    def search(self, query: str) -> list:
        """Search registry by plate, owner, or vehicle."""
        query = query.upper()
        results = []
        for plate, info in self._registry.items():
            if (query in plate or
                query in info.get("owner", "").upper() or
                query in info.get("vehicle", "").upper()):
                results.append({"plate": plate, **info})
        return results
