"""
Reward function implementations for traffic signal control.
Each function maps traffic metrics to a scalar reward signal.
"""

import numpy as np
from typing import Dict, Any
from enum import Enum


class RewardType(str, Enum):
    """Available reward function types."""
    WAITING_TIME = "waiting_time"
    QUEUE_LENGTH = "queue_length"
    COMBINED = "combined"
    THROUGHPUT = "throughput"
    PRESSURE = "pressure"


class RewardFunction:
    """
    Configurable reward function for traffic signal RL.
    
    Usage:
        reward_fn = RewardFunction(RewardType.COMBINED)
        reward = reward_fn.calculate(metrics, prev_metrics)
    """
    
    def __init__(self, reward_type: RewardType = RewardType.COMBINED, weights: Dict = None):
        self.reward_type = reward_type
        self.weights = weights or {
            "waiting_time": 1.0,
            "queue": 0.5,
            "throughput": 0.3,
            "switch_penalty": 0.2,
            "starvation_penalty": 0.5,
        }
    
    def calculate(
        self,
        current_metrics: Dict[str, Any],
        previous_metrics: Dict[str, Any],
        phase_changed: bool = False,
    ) -> float:
        """
        Calculate reward based on current and previous traffic metrics.
        
        Args:
            current_metrics: Dict with keys:
                - total_waiting_time: sum of waiting times across lanes
                - total_queue: total halted vehicles
                - throughput: vehicles that passed through
                - max_lane_wait: maximum wait time on any lane
            previous_metrics: Same dict from previous step
            phase_changed: Whether the agent switched phases
            
        Returns:
            Scalar reward value
        """
        if self.reward_type == RewardType.WAITING_TIME:
            return self._waiting_time_reward(current_metrics, previous_metrics)
        elif self.reward_type == RewardType.QUEUE_LENGTH:
            return self._queue_reward(current_metrics)
        elif self.reward_type == RewardType.THROUGHPUT:
            return self._throughput_reward(current_metrics, previous_metrics)
        elif self.reward_type == RewardType.PRESSURE:
            return self._pressure_reward(current_metrics)
        elif self.reward_type == RewardType.COMBINED:
            return self._combined_reward(
                current_metrics, previous_metrics, phase_changed
            )
        else:
            return self._waiting_time_reward(current_metrics, previous_metrics)
    
    def _waiting_time_reward(
        self, current: Dict, previous: Dict
    ) -> float:
        """
        Reward = reduction in total waiting time.
        Positive when waiting time decreases, negative when it increases.
        """
        prev_wait = previous.get("total_waiting_time", 0)
        curr_wait = current.get("total_waiting_time", 0)
        
        # Normalize by a factor to keep rewards in reasonable range
        reward = (prev_wait - curr_wait) / 100.0
        return float(np.clip(reward, -2.0, 2.0))
    
    def _queue_reward(self, current: Dict) -> float:
        """
        Reward = negative normalized queue length.
        Always negative, closer to 0 is better.
        """
        total_queue = current.get("total_queue", 0)
        num_lanes = current.get("num_lanes", 8)
        
        # Normalize by number of lanes and max expected queue
        reward = -total_queue / (num_lanes * 10.0)
        return float(np.clip(reward, -2.0, 0.0))
    
    def _throughput_reward(self, current: Dict, previous: Dict) -> float:
        """
        Reward = number of vehicles that passed through.
        Encourages maximizing flow.
        """
        throughput = current.get("throughput", 0)
        return float(throughput * 0.1)
    
    def _pressure_reward(self, current: Dict) -> float:
        """
        Max-pressure inspired reward.
        Reward = negative of maximum lane pressure.
        Pressure = upstream_queue - downstream_queue for each movement.
        """
        lane_queues = current.get("lane_queues", [])
        if not lane_queues:
            return 0.0
        
        max_pressure = max(lane_queues) - min(lane_queues)
        return float(-max_pressure / 20.0)
    
    def _combined_reward(
        self, current: Dict, previous: Dict, phase_changed: bool
    ) -> float:
        """
        Combined reward with multiple objectives:
        R = w1 * wait_reduction + w2 * (-queue) + w3 * throughput 
            - w4 * switch_penalty - w5 * starvation_penalty
        """
        w = self.weights
        
        # Component 1: Waiting time reduction
        wait_reward = self._waiting_time_reward(current, previous)
        
        # Component 2: Queue penalty
        queue_reward = self._queue_reward(current)
        
        # Component 3: Throughput bonus
        throughput = current.get("throughput", 0) * 0.05
        
        # Component 4: Phase switch penalty (discourages rapid switching)
        switch_penalty = -w["switch_penalty"] if phase_changed else 0.0
        
        # Component 5: Starvation penalty (punish very long waits on any lane)
        max_wait = current.get("max_lane_wait", 0)
        starvation = 0.0
        if max_wait > 120:  # More than 2 minutes
            starvation = -w["starvation_penalty"] * (max_wait - 120) / 60.0
        
        reward = (
            w["waiting_time"] * wait_reward
            + w["queue"] * queue_reward
            + w["throughput"] * throughput
            + switch_penalty
            + starvation
        )
        
        return float(np.clip(reward, -5.0, 5.0))


class AdaptiveRewardFunction(RewardFunction):
    """
    Reward function that adapts weights during training.
    Starts with simple reward (waiting time only), gradually
    introduces complexity (throughput, fairness).
    """
    
    def __init__(self, total_episodes: int = 1000):
        super().__init__(RewardType.COMBINED)
        self.total_episodes = total_episodes
        self.current_episode = 0
    
    def set_episode(self, episode: int):
        """Update current episode to adjust weights."""
        self.current_episode = episode
        progress = min(episode / self.total_episodes, 1.0)
        
        # Gradually increase complexity
        self.weights = {
            "waiting_time": 1.0,  # Always primary
            "queue": 0.3 + 0.2 * progress,  # Increases
            "throughput": 0.1 + 0.3 * progress,  # Increases
            "switch_penalty": 0.1 + 0.2 * progress,  # Increases
            "starvation_penalty": 0.2 + 0.4 * progress,  # Increases
        }
