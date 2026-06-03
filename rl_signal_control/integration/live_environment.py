"""
Live Traffic Environment: Real-time RL using camera feeds instead of SUMO.

Replaces the SUMO simulation with live camera data:
  Camera → YOLO → Bridge → State → RL Agent → Signal Controller

This is the production deployment of the RL agent.
"""

import time
import asyncio
import numpy as np
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
import logging

from rl_signal_control.integration.cv_to_rl_bridge import CVtoRLBridge
from rl_signal_control.integration.signal_controller import SignalController, ControlMode

logger = logging.getLogger(__name__)


@dataclass
class LiveEnvConfig:
    """Configuration for live environment."""
    decision_interval: float = 5.0      # Seconds between RL decisions
    min_green: int = 10                  # Minimum green time
    max_green: int = 60                  # Maximum green time
    yellow_time: int = 3                 # Yellow transition
    num_phases: int = 4                  # Signal phases
    control_mode: str = "simulated"      # simulated/hardware/api
    model_path: Optional[str] = None     # Path to trained RL model
    agent_type: str = "dqn"              # dqn or ppo


class LiveTrafficEnv:
    """
    Live traffic environment that connects all components:
    
    ┌─────────┐     ┌──────────┐     ┌─────────────┐     ┌────────────┐
    │  Camera  │────▶│  YOLO    │────▶│  CV→RL      │────▶│  RL Agent  │
    │  Feed    │     │  Detect  │     │  Bridge     │     │  (DQN/PPO) │
    └─────────┘     └──────────┘     └─────────────┘     └─────┬──────┘
                                                                │
                                                                ▼
    ┌─────────┐     ┌──────────┐     ┌─────────────┐     ┌────────────┐
    │Dashboard │◀────│  Events  │◀────│  Signal     │◀────│   Action   │
    │  (WS)   │     │  Broadcast│     │  Controller │     │  (phase)   │
    └─────────┘     └──────────┘     └─────────────┘     └────────────┘
    
    Usage:
        env = LiveTrafficEnv(config)
        env.set_detector(yolo_detector)
        env.start()  # Begins control loop
    """
    
    def __init__(self, config: LiveEnvConfig = None):
        self.config = config or LiveEnvConfig()
        
        # Components (injected)
        self._detector = None          # YOLODetector instance
        self._tracker = None           # Object tracker (for waiting time)
        self._speed_estimator = None   # Speed estimation module
        
        # Core components (created internally)
        self._bridge = CVtoRLBridge.create_default_4way()
        self._controller = SignalController(
            mode=ControlMode(self.config.control_mode),
            num_phases=self.config.num_phases,
            yellow_time=self.config.yellow_time,
            min_green=self.config.min_green,
            max_green=self.config.max_green,
        )
        self._agent = None
        
        # State
        self._is_running = False
        self._current_frame = None
        self._current_detections = []
        self._last_decision_time = 0
        self._decisions_made = 0
        self._total_reward = 0.0
        
        # Metrics history
        self._metrics_history = []
        
        # Event callback (for WebSocket broadcast)
        self._event_callback: Optional[Callable] = None
    
    def set_detector(self, detector):
        """Inject YOLO detector from ai_engine."""
        self._detector = detector
        logger.info("Detector connected to LiveTrafficEnv")
    
    def set_tracker(self, tracker):
        """Inject object tracker from ai_engine."""
        self._tracker = tracker
        logger.info("Tracker connected to LiveTrafficEnv")
    
    def set_speed_estimator(self, estimator):
        """Inject speed estimator from ai_engine."""
        self._speed_estimator = estimator
    
    def set_event_callback(self, callback: Callable):
        """Set callback for broadcasting events (to WebSocket/dashboard)."""
        self._event_callback = callback
    
    def load_agent(self, agent_type: str = None, model_path: str = None):
        """
        Load a trained RL agent.
        
        Args:
            agent_type: 'dqn' or 'ppo'
            model_path: Path to saved model weights
        """
        agent_type = agent_type or self.config.agent_type
        model_path = model_path or self.config.model_path
        
        state_size = self._bridge.state_size
        action_size = self.config.num_phases
        
        if agent_type == "dqn":
            from rl_signal_control.agents.dqn_agent import DQNAgent
            self._agent = DQNAgent(state_size=state_size, action_size=action_size)
        elif agent_type == "ppo":
            from rl_signal_control.agents.ppo_agent import PPOAgent
            self._agent = PPOAgent(state_size=state_size, action_size=action_size)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        if model_path:
            self._agent.load(model_path)
            logger.info(f"Loaded {agent_type} model from {model_path}")
        else:
            logger.warning("No model path provided - agent will use random/initial policy")
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Process a single camera frame through the full pipeline.
        Called by the existing video processing loop.
        
        Args:
            frame: BGR frame from camera/video
            
        Returns:
            Dict with RL decision info
        """
        self._current_frame = frame
        result = {"action_taken": False}
        
        if not self._agent or not self._detector:
            return result
        
        # Step 1: Detect vehicles
        detections = self._detector.detect(frame)
        self._current_detections = detections
        vehicles = self._detector.filter_vehicles(detections)
        
        # Step 2: Get tracked objects and speeds (if available)
        tracked = None
        speeds = None
        if self._tracker:
            tracked = self._tracker.get_tracks()
        if self._speed_estimator:
            speeds = self._speed_estimator.get_speeds()
        
        # Step 3: Convert to RL state
        state = self._bridge.detections_to_state(
            detections=vehicles,
            current_phase=self._controller.current_phase,
            tracked_objects=tracked,
            speeds=speeds,
        )
        
        # Step 4: Make decision (at configured interval)
        current_time = time.time()
        if current_time - self._last_decision_time >= self.config.decision_interval:
            # RL agent selects action
            action = self._agent.select_action(state, training=False)
            
            # Apply to signal controller
            transition_result = self._controller.set_phase(action)
            
            self._last_decision_time = current_time
            self._decisions_made += 1
            
            result = {
                "action_taken": True,
                "action": action,
                "phase_name": self._controller.get_state()["phase_name"],
                "transition": transition_result,
                "vehicles_detected": len(vehicles),
                "decision_number": self._decisions_made,
            }
            
            # Broadcast to dashboard
            self._broadcast_decision(result, state)
            
            logger.debug(f"RL Decision #{self._decisions_made}: phase={action} | vehicles={len(vehicles)}")
        
        # Record metrics
        self._record_metrics(vehicles, state)
        
        return result
    
    def _broadcast_decision(self, result: Dict, state: np.ndarray):
        """Broadcast RL decision to dashboard via WebSocket."""
        if self._event_callback:
            event = {
                "type": "rl_decision",
                "data": {
                    "decision": result,
                    "controller_state": self._controller.get_state(),
                    "bridge_metrics": self._bridge.get_metrics_summary(),
                    "timestamp": time.time(),
                }
            }
            try:
                self._event_callback(event)
            except Exception as e:
                logger.error(f"Failed to broadcast: {e}")
    
    def _record_metrics(self, vehicles: list, state: np.ndarray):
        """Record metrics for analysis."""
        metrics = {
            "timestamp": time.time(),
            "vehicle_count": len(vehicles),
            "current_phase": self._controller.current_phase,
            "phase_duration": self._controller.phase_duration,
            "signal_state": self._controller.signal_state.value,
            "queue_estimate": float(np.sum(state[:self._bridge.num_lanes])) * 50,
        }
        self._metrics_history.append(metrics)
        
        # Keep last 1000 records
        if len(self._metrics_history) > 1000:
            self._metrics_history = self._metrics_history[-1000:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get full system status for dashboard."""
        return {
            "is_running": self._is_running,
            "agent_loaded": self._agent is not None,
            "agent_type": self.config.agent_type,
            "detector_connected": self._detector is not None,
            "tracker_connected": self._tracker is not None,
            "decisions_made": self._decisions_made,
            "control_mode": self.config.control_mode,
            "decision_interval": self.config.decision_interval,
            "controller": self._controller.get_state(),
            "statistics": self._controller.get_statistics(),
        }
    
    def get_metrics_history(self, last_n: int = 100) -> list:
        """Get recent metrics for charting."""
        return self._metrics_history[-last_n:]
    
    def start(self):
        """Start the live control loop."""
        self._is_running = True
        logger.info("🚦 LiveTrafficEnv started - RL control active")
    
    def stop(self):
        """Stop the live control loop."""
        self._is_running = False
        logger.info("🛑 LiveTrafficEnv stopped")
    
    def reset_statistics(self):
        """Reset all statistics counters."""
        self._decisions_made = 0
        self._total_reward = 0.0
        self._metrics_history.clear()
