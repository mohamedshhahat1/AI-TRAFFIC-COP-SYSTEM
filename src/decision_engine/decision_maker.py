"""
Decision Maker Module
Classifies violation severity, filters false positives, and prioritizes actions.
"""

from typing import List, Dict, Optional
from loguru import logger
import time
from collections import deque

from src.violation_detection.violation import Violation, ViolationType, Severity


class DecisionMaker:
    """
    AI Decision-Making Engine for traffic violations.
    
    Responsibilities:
    - Classify severity levels
    - Filter false positives
    - Prioritize critical violations
    - Aggregate repeated violations
    - Decide on appropriate actions
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize decision maker.
        
        Args:
            config: Configuration for severity thresholds and rules
        """
        self.config = config or self._default_config()
        
        # Decision history
        self.decisions: List[dict] = []
        self.recent_violations: deque = deque(maxlen=100)
        
        # False positive tracking
        self.fp_candidates: Dict[str, int] = {}
        
        # Priority queue
        self.priority_queue: List[Violation] = []
        
        logger.info("DecisionMaker initialized")
    
    def _default_config(self) -> dict:
        """Default decision-making configuration."""
        return {
            "severity_thresholds": {
                "low": 0.3,
                "medium": 0.6,
                "high": 0.8,
            },
            "false_positive_threshold": 0.7,
            "min_confidence": 0.6,
            "escalation_rules": {
                "speed_critical_threshold": 40,  # km/h over limit
                "repeat_offender_count": 3,
                "high_priority_types": ["red_light_violation", "speed_violation"],
            },
            "actions": {
                "low": ["log", "record"],
                "medium": ["log", "record", "alert"],
                "high": ["log", "record", "alert", "notify_authority"],
                "critical": ["log", "record", "alert", "notify_authority", "dispatch"],
            },
        }
    
    def process_violation(self, violation: Violation) -> dict:
        """
        Process a violation through the decision pipeline.
        
        Args:
            violation: Detected violation to process
            
        Returns:
            Decision dictionary with actions and metadata
        """
        # Step 1: Validate (filter false positives)
        if not self._validate_violation(violation):
            return {
                "status": "rejected",
                "reason": "false_positive",
                "violation_id": violation.violation_id,
            }
        
        # Step 2: Classify severity
        severity = self._classify_severity(violation)
        violation.severity = severity
        
        # Step 3: Check for repeat offenders
        is_repeat = self._check_repeat_offender(violation)
        if is_repeat:
            # Escalate severity for repeat offenders
            severity = self._escalate_severity(severity)
            violation.severity = severity
        
        # Step 4: Determine actions
        actions = self._determine_actions(violation)
        
        # Step 5: Calculate priority score
        priority = self._calculate_priority(violation)
        
        # Step 6: Create decision record
        decision = {
            "status": "confirmed",
            "violation_id": violation.violation_id,
            "violation_type": violation.violation_type.value,
            "severity": severity.value,
            "priority_score": priority,
            "actions": actions,
            "is_repeat_offender": is_repeat,
            "timestamp": time.time(),
            "track_id": violation.track_id,
            "description": violation.description,
        }
        
        # Store decision
        self.decisions.append(decision)
        self.recent_violations.append(violation)
        
        # Add to priority queue if high priority
        if priority > 0.7:
            self.priority_queue.append(violation)
            self.priority_queue.sort(
                key=lambda v: self._calculate_priority(v), reverse=True
            )
        
        violation.is_confirmed = True
        
        logger.info(
            f"Decision: {violation.violation_type.value} | "
            f"Severity: {severity.value} | Priority: {priority:.2f} | "
            f"Actions: {actions}"
        )
        
        return decision
    
    def _validate_violation(self, violation: Violation) -> bool:
        """
        Validate violation and filter false positives.
        
        Args:
            violation: Violation to validate
            
        Returns:
            True if violation is likely genuine
        """
        # Check minimum confidence
        if violation.confidence < self.config["min_confidence"]:
            logger.debug(
                f"Violation rejected: low confidence ({violation.confidence:.2f})"
            )
            return False
        
        # Check for physically impossible speeds
        if violation.violation_type == ViolationType.SPEED:
            if violation.speed > 300:  # Impossible speed
                logger.debug(f"Violation rejected: impossible speed ({violation.speed})")
                return False
            if violation.speed < 0:
                return False
        
        # Check bounding box validity
        x1, y1, x2, y2 = violation.bbox
        if x2 - x1 < 10 or y2 - y1 < 10:
            logger.debug("Violation rejected: tiny bounding box")
            return False
        
        return True
    
    def _classify_severity(self, violation: Violation) -> Severity:
        """
        Classify violation severity based on type and parameters.
        
        Args:
            violation: Violation to classify
            
        Returns:
            Severity level
        """
        if violation.violation_type == ViolationType.SPEED:
            excess = violation.speed_excess
            if excess > 40:
                return Severity.CRITICAL
            elif excess > 20:
                return Severity.HIGH
            elif excess > 10:
                return Severity.MEDIUM
            else:
                return Severity.LOW
        
        elif violation.violation_type == ViolationType.RED_LIGHT:
            # Red light violations are always at least HIGH
            if violation.speed > 50:
                return Severity.CRITICAL
            return Severity.HIGH
        
        elif violation.violation_type == ViolationType.LANE:
            if violation.speed > 80:
                return Severity.HIGH
            return Severity.MEDIUM
        
        elif violation.violation_type == ViolationType.ILLEGAL_PARKING:
            return Severity.LOW
        
        return Severity.MEDIUM
    
    def _check_repeat_offender(self, violation: Violation) -> bool:
        """Check if this vehicle is a repeat offender."""
        threshold = self.config["escalation_rules"]["repeat_offender_count"]
        
        count = sum(
            1 for v in self.recent_violations
            if v.track_id == violation.track_id
        )
        
        return count >= threshold
    
    def _escalate_severity(self, current: Severity) -> Severity:
        """Escalate severity by one level."""
        severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        current_idx = severity_order.index(current)
        
        if current_idx < len(severity_order) - 1:
            return severity_order[current_idx + 1]
        return current
    
    def _determine_actions(self, violation: Violation) -> List[str]:
        """Determine actions to take based on violation severity."""
        return self.config["actions"].get(
            violation.severity.value, ["log", "record"]
        )
    
    def _calculate_priority(self, violation: Violation) -> float:
        """
        Calculate priority score (0.0 to 1.0).
        
        Higher priority = needs immediate attention.
        """
        score = 0.0
        
        # Base score from severity
        severity_scores = {
            Severity.LOW: 0.2,
            Severity.MEDIUM: 0.4,
            Severity.HIGH: 0.7,
            Severity.CRITICAL: 1.0,
        }
        score = severity_scores.get(violation.severity, 0.3)
        
        # Boost for high-priority violation types
        high_priority = self.config["escalation_rules"]["high_priority_types"]
        if violation.violation_type.value in high_priority:
            score = min(1.0, score + 0.1)
        
        # Boost for high confidence
        score = score * (0.5 + 0.5 * violation.confidence)
        
        # Boost for high speed
        if violation.speed > 100:
            score = min(1.0, score + 0.15)
        
        return round(score, 2)
    
    def get_top_priorities(self, n: int = 5) -> List[Violation]:
        """Get top N priority violations."""
        return self.priority_queue[:n]
    
    def get_statistics(self) -> dict:
        """Get decision engine statistics."""
        total = len(self.decisions)
        confirmed = sum(1 for d in self.decisions if d["status"] == "confirmed")
        rejected = sum(1 for d in self.decisions if d["status"] == "rejected")
        
        return {
            "total_processed": total,
            "confirmed": confirmed,
            "rejected": rejected,
            "confirmation_rate": confirmed / total if total > 0 else 0,
            "priority_queue_size": len(self.priority_queue),
            "severity_distribution": self._get_severity_distribution(),
        }
    
    def _get_severity_distribution(self) -> Dict[str, int]:
        """Get distribution of confirmed violation severities."""
        dist = {}
        for decision in self.decisions:
            if decision["status"] == "confirmed":
                sev = decision["severity"]
                dist[sev] = dist.get(sev, 0) + 1
        return dist
    
    def clear(self):
        """Clear all decision history."""
        self.decisions.clear()
        self.recent_violations.clear()
        self.priority_queue.clear()
        self.fp_candidates.clear()
        logger.info("Decision engine cleared")
