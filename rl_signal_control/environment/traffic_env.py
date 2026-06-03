"""
Custom Gymnasium environment for traffic signal control using SUMO.
The RL agent observes traffic state and decides signal phases.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import os
import sys
from typing import Optional, Tuple, Dict, Any

# SUMO imports
if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import traci
import sumolib


class TrafficSignalEnv(gym.Env):
    """
    Traffic Signal Control Environment.
    
    The agent controls traffic signal phases at an intersection.
    It observes queue lengths, waiting times, and vehicle counts,
    then selects the next signal phase to minimize overall waiting time.
    
    State Space:
        - Queue length per lane (N lanes)
        - Average waiting time per lane (N lanes)
        - Current phase (one-hot, P phases)
        - Current phase duration (1 value)
        - Number of approaching vehicles per lane (N lanes)
        - Density per lane (N lanes)
    
    Action Space:
        - Discrete: select next phase (0 to P-1)
    
    Reward:
        - Negative of change in cumulative waiting time
        - Bonus for throughput
        - Penalty for phase switching
    """
    
    metadata = {"render_modes": ["human", "sumo-gui"]}
    
    def __init__(
        self,
        net_file: str,
        route_file: str,
        traffic_signal_id: str = "TL0",
        delta_time: int = 5,
        yellow_time: int = 3,
        min_green: int = 10,
        max_green: int = 60,
        reward_type: str = "waiting_time",
        use_gui: bool = False,
        max_steps: int = 3600,
        sumo_seed: int = 42,
    ):
        """
        Initialize the traffic signal environment.
        
        Args:
            net_file: Path to SUMO network file (.net.xml)
            route_file: Path to SUMO route file (.rou.xml)
            traffic_signal_id: ID of the traffic light to control
            delta_time: Simulation seconds between agent decisions
            yellow_time: Duration of yellow phase (seconds)
            min_green: Minimum green phase duration
            max_green: Maximum green phase duration
            reward_type: Type of reward function
            use_gui: Whether to open SUMO GUI
            max_steps: Maximum simulation steps per episode
            sumo_seed: Random seed for SUMO
        """
        super().__init__()
        
        self.net_file = net_file
        self.route_file = route_file
        self.ts_id = traffic_signal_id
        self.delta_time = delta_time
        self.yellow_time = yellow_time
        self.min_green = min_green
        self.max_green = max_green
        self.reward_type = reward_type
        self.use_gui = use_gui
        self.max_steps = max_steps
        self.sumo_seed = sumo_seed
        
        # Will be set after SUMO starts
        self._net = sumolib.net.readNet(net_file)
        self._sumo_running = False
        self._step_count = 0
        
        # Get traffic light info
        tl = self._net.getNode(traffic_signal_id) if self._net.getNode(traffic_signal_id) else None
        
        # Determine lanes controlled by this traffic light
        self.controlled_lanes = self._get_controlled_lanes()
        self.num_lanes = len(self.controlled_lanes) if self.controlled_lanes else 8
        
        # Phases (will be read from SUMO)
        self.num_phases = 4  # Default, updated on reset
        self.current_phase = 0
        self.current_phase_duration = 0
        self.is_yellow = False
        
        # Previous metrics for reward calculation
        self._prev_waiting_time = 0
        self._prev_total_wait = 0
        self._vehicles_passed = 0
        
        # Define spaces
        # State: queue(N) + wait_time(N) + phase(P) + duration(1) + approaching(N) + density(N)
        state_size = self.num_lanes * 4 + self.num_phases + 1
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(state_size,), dtype=np.float32
        )
        
        # Action: choose next phase
        self.action_space = spaces.Discrete(self.num_phases)
    
    def _get_controlled_lanes(self) -> list:
        """Get lanes controlled by the traffic signal from network file."""
        try:
            tls = self._net.getTrafficLights()
            for tl in tls:
                if tl.getID() == self.ts_id:
                    connections = tl.getConnections()
                    lanes = list(set(conn[0].getID() for conn in connections))
                    return sorted(lanes)
        except Exception:
            pass
        return []
    
    def _start_sumo(self):
        """Start SUMO simulation."""
        sumo_binary = "sumo-gui" if self.use_gui else "sumo"
        
        sumo_cmd = [
            sumo_binary,
            "-n", self.net_file,
            "-r", self.route_file,
            "--no-step-log", "true",
            "--waiting-time-memory", "1000",
            "--time-to-teleport", "-1",
            "--seed", str(self.sumo_seed),
        ]
        
        traci.start(sumo_cmd)
        self._sumo_running = True
        
        # Read actual phases from SUMO
        logic = traci.trafficlight.getAllProgramLogics(self.ts_id)
        if logic:
            self.num_phases = len([
                p for p in logic[0].phases 
                if "y" not in p.state.lower()
            ])
        
        # Update controlled lanes from running simulation
        self.controlled_lanes = list(
            traci.trafficlight.getControlledLanes(self.ts_id)
        )
        self.num_lanes = len(set(self.controlled_lanes))
    
    def _stop_sumo(self):
        """Stop SUMO simulation."""
        if self._sumo_running:
            traci.close()
            self._sumo_running = False
    
    def reset(
        self, *, seed: Optional[int] = None, options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset environment for new episode.
        
        Returns:
            observation: Initial state
            info: Additional info dict
        """
        super().reset(seed=seed)
        
        # Stop previous simulation if running
        self._stop_sumo()
        
        # Update seed if provided
        if seed is not None:
            self.sumo_seed = seed
        
        # Start new simulation
        self._start_sumo()
        
        # Reset internal state
        self._step_count = 0
        self.current_phase = 0
        self.current_phase_duration = 0
        self.is_yellow = False
        self._prev_waiting_time = 0
        self._prev_total_wait = 0
        self._vehicles_passed = 0
        
        # Get initial observation
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one agent action (signal phase change).
        
        Args:
            action: Next phase index to switch to
            
        Returns:
            observation, reward, terminated, truncated, info
        """
        assert self.action_space.contains(action), f"Invalid action: {action}"
        
        # Apply action (phase change)
        if action != self.current_phase:
            # Insert yellow phase before switching
            self._set_yellow_phase()
            self._simulate(self.yellow_time)
            
            # Switch to new phase
            self._set_green_phase(action)
            self.current_phase = action
            self.current_phase_duration = 0
        
        # Simulate for delta_time seconds
        self._simulate(self.delta_time)
        self.current_phase_duration += self.delta_time
        self._step_count += 1
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Get new observation
        observation = self._get_observation()
        
        # Check termination
        terminated = self._step_count >= self.max_steps
        truncated = False
        
        # Check if simulation ended (no more vehicles)
        if traci.simulation.getMinExpectedNumber() <= 0:
            terminated = True
        
        info = self._get_info()
        
        return observation, reward, terminated, truncated, info
    
    def _simulate(self, num_seconds: int):
        """Run SUMO simulation for given seconds."""
        for _ in range(num_seconds):
            traci.simulationStep()
    
    def _set_yellow_phase(self):
        """Set traffic light to yellow (all directions)."""
        yellow_state = "y" * len(
            traci.trafficlight.getRedYellowGreenState(self.ts_id)
        )
        traci.trafficlight.setRedYellowGreenState(self.ts_id, yellow_state)
        self.is_yellow = True
    
    def _set_green_phase(self, phase_index: int):
        """Set traffic light to specified green phase."""
        traci.trafficlight.setPhase(self.ts_id, phase_index)
        self.is_yellow = False
    
    def _get_observation(self) -> np.ndarray:
        """
        Construct state observation vector.
        
        Normalized to [0, 1] range for neural network input.
        """
        lanes = list(set(self.controlled_lanes))
        
        # Queue lengths (normalized by max ~50 vehicles)
        queue_lengths = np.array([
            traci.lane.getLastStepHaltingNumber(lane) / 50.0
            for lane in lanes
        ], dtype=np.float32)
        
        # Average waiting time per lane (normalized by max ~200s)
        waiting_times = np.array([
            traci.lane.getWaitingTime(lane) / 200.0
            for lane in lanes
        ], dtype=np.float32)
        
        # Number of approaching vehicles (normalized by max ~30)
        approaching = np.array([
            traci.lane.getLastStepVehicleNumber(lane) / 30.0
            for lane in lanes
        ], dtype=np.float32)
        
        # Lane density (occupancy 0-100%)
        density = np.array([
            traci.lane.getLastStepOccupancy(lane) / 100.0
            for lane in lanes
        ], dtype=np.float32)
        
        # Current phase (one-hot)
        phase_one_hot = np.zeros(self.num_phases, dtype=np.float32)
        if self.current_phase < self.num_phases:
            phase_one_hot[self.current_phase] = 1.0
        
        # Phase duration (normalized by max_green)
        duration = np.array(
            [self.current_phase_duration / self.max_green], dtype=np.float32
        )
        
        # Clip all values to [0, 1]
        observation = np.concatenate([
            np.clip(queue_lengths, 0, 1),
            np.clip(waiting_times, 0, 1),
            phase_one_hot,
            np.clip(duration, 0, 1),
            np.clip(approaching, 0, 1),
            np.clip(density, 0, 1),
        ])
        
        # Pad or truncate to match observation space
        expected_size = self.observation_space.shape[0]
        if len(observation) < expected_size:
            observation = np.pad(observation, (0, expected_size - len(observation)))
        elif len(observation) > expected_size:
            observation = observation[:expected_size]
        
        return observation.astype(np.float32)
    
    def _calculate_reward(self) -> float:
        """
        Calculate reward based on traffic metrics.
        
        Primary: negative change in total waiting time
        Secondary: throughput bonus, switching penalty
        """
        # Total waiting time across all lanes
        lanes = list(set(self.controlled_lanes))
        total_wait = sum(traci.lane.getWaitingTime(lane) for lane in lanes)
        
        # Total queue length
        total_queue = sum(
            traci.lane.getLastStepHaltingNumber(lane) for lane in lanes
        )
        
        # Vehicles that departed (throughput)
        departed = traci.simulation.getDepartedNumber()
        
        if self.reward_type == "waiting_time":
            # Reward = reduction in waiting time
            reward = (self._prev_total_wait - total_wait) / 100.0
            
        elif self.reward_type == "queue":
            # Reward = negative queue length
            reward = -total_queue / (self.num_lanes * 10.0)
            
        elif self.reward_type == "combined":
            # Combined: waiting time + throughput + queue
            wait_reward = (self._prev_total_wait - total_wait) / 100.0
            throughput_reward = departed * 0.05
            queue_penalty = -total_queue / (self.num_lanes * 20.0)
            reward = wait_reward + throughput_reward + queue_penalty
            
        else:
            reward = -total_wait / 1000.0
        
        # Update previous values
        self._prev_total_wait = total_wait
        self._vehicles_passed += departed
        
        return float(reward)
    
    def _get_info(self) -> Dict[str, Any]:
        """Get additional info for logging."""
        lanes = list(set(self.controlled_lanes))
        
        total_wait = sum(traci.lane.getWaitingTime(lane) for lane in lanes)
        total_queue = sum(
            traci.lane.getLastStepHaltingNumber(lane) for lane in lanes
        )
        
        return {
            "step": self._step_count,
            "total_waiting_time": total_wait,
            "total_queue_length": total_queue,
            "vehicles_passed": self._vehicles_passed,
            "current_phase": self.current_phase,
            "phase_duration": self.current_phase_duration,
            "simulation_time": traci.simulation.getTime(),
        }
    
    def render(self):
        """Rendering handled by SUMO GUI if use_gui=True."""
        pass
    
    def close(self):
        """Clean up SUMO connection."""
        self._stop_sumo()
    
    def __del__(self):
        """Destructor to ensure SUMO is closed."""
        self.close()
