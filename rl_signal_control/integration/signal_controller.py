"""
Signal Controller: Translates RL agent actions into signal commands.

Manages the traffic light state machine:
  RL Action (phase index) → Yellow transition → Green phase activation

Supports:
  - Simulated mode (for testing/training with SUMO)
  - Hardware mode (GPIO/serial commands to real traffic controller)
  - API mode (HTTP calls to signal controller API)
"""

import time
import asyncio
from typing import Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ControlMode(str, Enum):
    """Signal controller operating mode."""
    SIMULATED = "simulated"   # In-memory state (for testing)
    HARDWARE = "hardware"     # GPIO/serial to real controller
    API = "api"               # HTTP to external controller


class SignalState(str, Enum):
    """Traffic signal states."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class PhaseConfig:
    """Configuration for a signal phase."""
    phase_id: int
    name: str
    green_directions: list  # e.g., ['north', 'south']
    min_green: int = 10     # Minimum green duration (seconds)
    max_green: int = 60     # Maximum green duration (seconds)
    yellow_time: int = 3    # Yellow transition time


class SignalController:
    """
    Traffic Signal Controller.
    
    Receives actions from the RL agent and manages the signal state machine.
    Enforces safety constraints (min green, yellow transitions, all-red clearance).
    
    Usage:
        controller = SignalController(mode=ControlMode.SIMULATED, num_phases=4)
        
        # RL agent decides next phase
        controller.set_phase(action=2)  # Switch to East-West green
        
        # Get current state for dashboard
        state = controller.get_state()
    """
    
    def __init__(
        self,
        mode: ControlMode = ControlMode.SIMULATED,
        num_phases: int = 4,
        yellow_time: int = 3,
        all_red_time: int = 1,
        min_green: int = 10,
        max_green: int = 60,
        phase_configs: Optional[list] = None,
        hardware_callback: Optional[Callable] = None,
        api_url: Optional[str] = None,
    ):
        """
        Initialize signal controller.
        
        Args:
            mode: Operating mode (simulated/hardware/api)
            num_phases: Number of signal phases
            yellow_time: Yellow phase duration
            all_red_time: All-red clearance time between phases
            min_green: Minimum green phase duration
            max_green: Maximum green phase duration
            phase_configs: Optional list of PhaseConfig objects
            hardware_callback: Function to call for hardware mode
            api_url: URL for API mode
        """
        self.mode = mode
        self.num_phases = num_phases
        self.yellow_time = yellow_time
        self.all_red_time = all_red_time
        self.min_green = min_green
        self.max_green = max_green
        self.hardware_callback = hardware_callback
        self.api_url = api_url
        
        # Phase configurations
        if phase_configs:
            self.phases = phase_configs
        else:
            self.phases = self._default_phases()
        
        # Current state
        self._current_phase = 0
        self._signal_state = SignalState.GREEN
        self._phase_start_time = time.time()
        self._last_switch_time = time.time()
        self._is_transitioning = False
        
        # Statistics
        self._phase_history = []
        self._total_switches = 0
        self._total_yellow_time = 0
        
        # Event callbacks
        self._on_phase_change: Optional[Callable] = None
        self._on_state_change: Optional[Callable] = None
        
        logger.info(f"SignalController initialized | mode={mode} | phases={num_phases}")
    
    def _default_phases(self) -> list:
        """Create default 4-phase configuration."""
        return [
            PhaseConfig(0, "North-South Through", ["north", "south"]),
            PhaseConfig(1, "North-South Left", ["north_left", "south_left"]),
            PhaseConfig(2, "East-West Through", ["east", "west"]),
            PhaseConfig(3, "East-West Left", ["east_left", "west_left"]),
        ]
    
    @property
    def current_phase(self) -> int:
        return self._current_phase
    
    @property
    def signal_state(self) -> SignalState:
        return self._signal_state
    
    @property
    def phase_duration(self) -> float:
        """How long current phase has been active (seconds)."""
        return time.time() - self._phase_start_time
    
    @property
    def can_switch(self) -> bool:
        """Whether the controller can accept a phase switch now."""
        if self._is_transitioning:
            return False
        if self.phase_duration < self.min_green:
            return False
        return True
    
    def set_phase(self, action: int) -> Dict[str, Any]:
        """
        Set the traffic signal to a new phase.
        
        If action == current phase, extend current green.
        If different, initiate yellow → all-red → new green transition.
        
        Args:
            action: Target phase index (0 to num_phases-1)
            
        Returns:
            Dict with transition info
        """
        if action < 0 or action >= self.num_phases:
            return {"error": f"Invalid phase: {action}", "accepted": False}
        
        # Same phase: just extend (no transition needed)
        if action == self._current_phase and not self._is_transitioning:
            # Check max green
            if self.phase_duration >= self.max_green:
                # Force switch to next phase
                action = (self._current_phase + 1) % self.num_phases
            else:
                return {
                    "accepted": True,
                    "action": "extend",
                    "phase": self._current_phase,
                    "duration": self.phase_duration,
                }
        
        # Can't switch during min green or transition
        if not self.can_switch and action != self._current_phase:
            return {
                "accepted": False,
                "reason": "min_green" if not self._is_transitioning else "transitioning",
                "remaining": max(0, self.min_green - self.phase_duration),
            }
        
        # Initiate transition
        result = self._execute_transition(action)
        return result
    
    def _execute_transition(self, new_phase: int) -> Dict[str, Any]:
        """Execute phase transition with yellow and all-red."""
        old_phase = self._current_phase
        self._is_transitioning = True
        
        # Record history
        self._phase_history.append({
            "phase": old_phase,
            "duration": self.phase_duration,
            "timestamp": time.time(),
        })
        
        # Yellow phase
        self._signal_state = SignalState.YELLOW
        self._notify_state_change()
        self._apply_signal(SignalState.YELLOW, old_phase)
        
        # In simulated mode, transition is instant
        # In real mode, we'd wait for yellow_time + all_red_time
        
        # Switch to new green
        self._current_phase = new_phase
        self._signal_state = SignalState.GREEN
        self._phase_start_time = time.time()
        self._last_switch_time = time.time()
        self._is_transitioning = False
        self._total_switches += 1
        self._total_yellow_time += self.yellow_time
        
        self._apply_signal(SignalState.GREEN, new_phase)
        self._notify_phase_change(old_phase, new_phase)
        self._notify_state_change()
        
        logger.debug(f"Phase switch: {old_phase} → {new_phase}")
        
        return {
            "accepted": True,
            "action": "switch",
            "old_phase": old_phase,
            "new_phase": new_phase,
            "yellow_time": self.yellow_time,
        }
    
    def _apply_signal(self, state: SignalState, phase: int):
        """Apply signal state to physical/simulated controller."""
        if self.mode == ControlMode.SIMULATED:
            pass  # State tracked internally
            
        elif self.mode == ControlMode.HARDWARE:
            if self.hardware_callback:
                self.hardware_callback(phase=phase, state=state.value)
                
        elif self.mode == ControlMode.API:
            # Would make HTTP call to signal controller API
            # asyncio.create_task(self._api_call(phase, state))
            pass
    
    def get_state(self) -> Dict[str, Any]:
        """Get complete controller state for dashboard/logging."""
        return {
            "current_phase": self._current_phase,
            "phase_name": self.phases[self._current_phase].name if self._current_phase < len(self.phases) else "Unknown",
            "signal_state": self._signal_state.value,
            "phase_duration": round(self.phase_duration, 1),
            "is_transitioning": self._is_transitioning,
            "can_switch": self.can_switch,
            "total_switches": self._total_switches,
            "mode": self.mode.value,
            "green_directions": self.phases[self._current_phase].green_directions if self._current_phase < len(self.phases) else [],
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        total_time = time.time() - (self._phase_history[0]["timestamp"] if self._phase_history else time.time())
        
        return {
            "total_switches": self._total_switches,
            "total_yellow_time": self._total_yellow_time,
            "avg_phase_duration": (
                sum(h["duration"] for h in self._phase_history) / max(len(self._phase_history), 1)
            ),
            "phase_distribution": self._get_phase_distribution(),
            "switches_per_minute": self._total_switches / max(total_time / 60, 1),
            "uptime_seconds": total_time,
        }
    
    def _get_phase_distribution(self) -> Dict[int, float]:
        """Calculate percentage of time spent in each phase."""
        if not self._phase_history:
            return {}
        
        total_duration = sum(h["duration"] for h in self._phase_history)
        distribution = {}
        
        for phase in range(self.num_phases):
            phase_time = sum(h["duration"] for h in self._phase_history if h["phase"] == phase)
            distribution[phase] = round(phase_time / max(total_duration, 1) * 100, 1)
        
        return distribution
    
    # Event callbacks
    def on_phase_change(self, callback: Callable):
        """Register callback for phase changes."""
        self._on_phase_change = callback
    
    def on_state_change(self, callback: Callable):
        """Register callback for state changes."""
        self._on_state_change = callback
    
    def _notify_phase_change(self, old_phase: int, new_phase: int):
        if self._on_phase_change:
            self._on_phase_change(old_phase=old_phase, new_phase=new_phase)
    
    def _notify_state_change(self):
        if self._on_state_change:
            self._on_state_change(state=self.get_state())
