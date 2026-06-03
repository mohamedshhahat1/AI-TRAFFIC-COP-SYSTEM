"""
Baseline agents for comparison with RL agents.
These implement traditional traffic signal control strategies.
"""

import numpy as np
from typing import Dict, Any, Optional


class FixedTimeAgent:
    """
    Fixed-time signal control baseline.
    Cycles through phases with fixed durations.
    This is the simplest and most common real-world strategy.
    """
    
    def __init__(
        self,
        num_phases: int = 4,
        phase_duration: int = 30,
        yellow_time: int = 3,
    ):
        self.num_phases = num_phases
        self.phase_duration = phase_duration
        self.yellow_time = yellow_time
        self.current_phase = 0
        self.time_in_phase = 0
    
    def select_action(self, state: np.ndarray = None, training: bool = False) -> int:
        """Always return next phase in cycle after fixed duration."""
        self.time_in_phase += 1
        
        if self.time_in_phase >= self.phase_duration:
            self.time_in_phase = 0
            self.current_phase = (self.current_phase + 1) % self.num_phases
        
        return self.current_phase
    
    def store_transition(self, *args, **kwargs):
        pass
    
    def train_step(self) -> None:
        return None
    
    def reset(self):
        self.current_phase = 0
        self.time_in_phase = 0


class MaxPressureAgent:
    """
    Max-Pressure signal control.
    Selects the phase that serves the lane with maximum 'pressure'.
    Pressure = upstream_queue - downstream_capacity.
    
    This is a well-known adaptive algorithm from transportation research.
    Reference: Varaiya (2013) "Max pressure control of a network of signalized intersections"
    """
    
    def __init__(self, num_phases: int = 4, num_lanes_per_phase: int = 2):
        self.num_phases = num_phases
        self.num_lanes_per_phase = num_lanes_per_phase
    
    def select_action(self, state: np.ndarray, training: bool = False) -> int:
        """
        Select phase with maximum pressure (longest queue).
        
        State format assumed:
            [queue_lane_0, queue_lane_1, ..., queue_lane_N, ...]
        """
        if state is None:
            return 0
        
        # Extract queue lengths (first N values in state)
        num_lanes = self.num_phases * self.num_lanes_per_phase
        queue_lengths = state[:num_lanes]
        
        # Calculate pressure per phase (sum of queues served by that phase)
        phase_pressures = np.zeros(self.num_phases)
        for phase in range(self.num_phases):
            start = phase * self.num_lanes_per_phase
            end = start + self.num_lanes_per_phase
            phase_pressures[phase] = np.sum(queue_lengths[start:end])
        
        # Select phase with maximum pressure
        return int(np.argmax(phase_pressures))
    
    def store_transition(self, *args, **kwargs):
        pass
    
    def train_step(self) -> None:
        return None


class ActuatedAgent:
    """
    Actuated signal control baseline.
    Extends current green phase if vehicles are still arriving,
    otherwise switches to next phase.
    
    Mimics SUMO's 'actuated' traffic light type.
    """
    
    def __init__(
        self,
        num_phases: int = 4,
        min_green: int = 10,
        max_green: int = 50,
        extension_time: int = 3,
        gap_threshold: float = 0.1,  # Density threshold to extend
    ):
        self.num_phases = num_phases
        self.min_green = min_green
        self.max_green = max_green
        self.extension_time = extension_time
        self.gap_threshold = gap_threshold
        self.current_phase = 0
        self.time_in_phase = 0
    
    def select_action(self, state: np.ndarray, training: bool = False) -> int:
        """
        Extend current phase if traffic is flowing, else switch.
        Uses density from state to detect vehicle presence.
        """
        self.time_in_phase += 1
        
        if state is None:
            return self._cycle_phase()
        
        # Extract density for current phase's lanes
        # Density is in the last quarter of the state vector
        state_len = len(state)
        num_lanes = state_len // 4  # Approximate
        density_start = state_len - num_lanes
        
        # Get density for lanes served by current phase
        lanes_per_phase = max(1, num_lanes // self.num_phases)
        start = density_start + self.current_phase * lanes_per_phase
        end = start + lanes_per_phase
        current_density = np.mean(state[start:end]) if end <= state_len else 0
        
        # Decision logic
        if self.time_in_phase < self.min_green:
            # Haven't reached minimum green yet
            return self.current_phase
        elif self.time_in_phase >= self.max_green:
            # Exceeded maximum, must switch
            return self._cycle_phase()
        elif current_density > self.gap_threshold:
            # Vehicles still flowing, extend
            return self.current_phase
        else:
            # Gap detected, switch to next phase
            return self._cycle_phase()
    
    def _cycle_phase(self) -> int:
        """Move to next phase in cycle."""
        self.current_phase = (self.current_phase + 1) % self.num_phases
        self.time_in_phase = 0
        return self.current_phase
    
    def store_transition(self, *args, **kwargs):
        pass
    
    def train_step(self) -> None:
        return None
    
    def reset(self):
        self.current_phase = 0
        self.time_in_phase = 0


class RandomAgent:
    """Random action baseline. Useful for sanity checking."""
    
    def __init__(self, num_phases: int = 4):
        self.num_phases = num_phases
    
    def select_action(self, state: np.ndarray = None, training: bool = False) -> int:
        return np.random.randint(0, self.num_phases)
    
    def store_transition(self, *args, **kwargs):
        pass
    
    def train_step(self) -> None:
        return None
