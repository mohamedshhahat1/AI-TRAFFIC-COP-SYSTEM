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
        """Create a sample vehicle registry with Egyptian plates."""
        return {
            "سعر1234": {"owner": "أحمد محمد", "vehicle": "تويوتا كورولا 2022", "color": "أبيض", "violations_history": 2},
            "قنا5678": {"owner": "محمد علي", "vehicle": "هيونداي إلنترا 2021", "color": "فضي", "violations_history": 0},
            "جمص9012": {"owner": "سارة حسن", "vehicle": "كيا سبورتاج 2023", "color": "أسود", "violations_history": 1},
            "طبع3456": {"owner": "عمر خالد", "vehicle": "نيسان صني 2020", "color": "أحمر", "violations_history": 5},
            "لمن7890": {"owner": "فاطمة إبراهيم", "vehicle": "تويوتا ياريس 2022", "color": "أزرق", "violations_history": 0},
            "وهد2345": {"owner": "حسن أحمد", "vehicle": "شيفروليه أوبترا 2019", "color": "رمادي", "violations_history": 3},
            "بحث6789": {"owner": "نور سعيد", "vehicle": "هيونداي أكسنت 2021", "color": "أبيض", "violations_history": 1},
            "عصم0123": {"owner": "يوسف طارق", "vehicle": "سوزوكي سويفت 2020", "color": "أخضر", "violations_history": 0},
        }

    def _save_registry(self):
        """Save registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self._registry, f, indent=2, ensure_ascii=False)
        logger.info(f"Registry saved: {len(self._registry)} entries")

    def _normalize_plate(self, plate: str) -> str:
        """Normalize plate for lookup: strip spaces, uppercase English."""
        return plate.replace(" ", "").upper().strip()

    def _build_lookup_index(self):
        """Build a normalized lookup index for the registry."""
        self._lookup_index = {}
        for plate_key in self._registry:
            normalized = self._normalize_plate(plate_key)
            self._lookup_index[normalized] = plate_key

    def lookup(self, plate_number: str) -> Optional[VehicleInfo]:
        """
        Look up a plate number in the registry.
        Handles both Arabic and English plates, with or without spaces.

        Args:
            plate_number: Cleaned plate string (e.g., "ABC1234" or "سعر1234")

        Returns:
            VehicleInfo if found, with registered=False if not in registry
        """
        if not hasattr(self, '_lookup_index'):
            self._build_lookup_index()

        normalized = self._normalize_plate(plate_number)

        # Try normalized lookup
        original_key = self._lookup_index.get(normalized)
        if original_key:
            entry = self._registry[original_key]
            return VehicleInfo(
                plate_number=plate_number,
                owner=entry.get("owner", "Unknown"),
                vehicle=entry.get("vehicle", "Unknown"),
                color=entry.get("color", "Unknown"),
                registered=True,
                violations_history=entry.get("violations_history", 0),
            )

        # Not in registry
        return VehicleInfo(
            plate_number=plate_number,
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
