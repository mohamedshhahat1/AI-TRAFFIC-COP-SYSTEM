"""
Deep Q-Network (DQN) Agent for traffic signal control.
Uses experience replay and target network for stable training.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
from typing import Optional


class QNetwork(nn.Module):
    """
    Neural network that approximates Q(s, a) for all actions.
    Architecture: Input → 128 → 128 → 64 → num_actions
    """
    
    def __init__(self, state_size: int, action_size: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.LayerNorm(128),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.LayerNorm(128),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_size),
        )
    
    def forward(self, x):
        return self.network(x)


class DQNAgent:
    """
    DQN Agent with:
    - Experience Replay Buffer
    - Target Network (soft update)
    - Epsilon-greedy exploration with decay
    - Double DQN (uses online network to select, target to evaluate)
    """
    
    def __init__(
        self,
        state_size: int,
        action_size: int,
        learning_rate: float = 1e-3,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_size: int = 100_000,
        batch_size: int = 64,
        tau: float = 0.005,
        update_every: int = 4,
        double_dqn: bool = True,
        device: Optional[str] = None,
    ):
        """
        Initialize DQN Agent.
        
        Args:
            state_size: Dimension of state space
            action_size: Number of discrete actions
            learning_rate: Learning rate for optimizer
            gamma: Discount factor for future rewards
            epsilon_start: Initial exploration rate
            epsilon_end: Minimum exploration rate
            epsilon_decay: Multiplicative decay per episode
            buffer_size: Maximum replay buffer size
            batch_size: Mini-batch size for training
            tau: Soft update coefficient for target network
            update_every: Steps between network updates
            double_dqn: Use Double DQN variant
            device: 'cuda' or 'cpu'
        """
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.tau = tau
        self.update_every = update_every
        self.double_dqn = double_dqn
        self.step_count = 0
        
        # Device
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Networks
        self.q_network = QNetwork(state_size, action_size).to(self.device)
        self.target_network = QNetwork(state_size, action_size).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Replay buffer
        self.memory = deque(maxlen=buffer_size)
        
        # Training stats
        self.losses = []
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        Select action using epsilon-greedy policy.
        
        Args:
            state: Current observation
            training: If False, always exploit (no exploration)
            
        Returns:
            Selected action index
        """
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_size - 1)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.q_network(state_tensor)
        
        return q_values.argmax(dim=1).item()
    
    def store_transition(
        self, state: np.ndarray, action: int, reward: float,
        next_state: np.ndarray, done: bool
    ):
        """Store transition in replay buffer."""
        self.memory.append((state, action, reward, next_state, done))
    
    def train_step(self) -> Optional[float]:
        """
        Sample batch from replay buffer and update Q-network.
        
        Returns:
            Loss value or None if buffer too small
        """
        self.step_count += 1
        
        # Only update every N steps
        if self.step_count % self.update_every != 0:
            return None
        
        # Need enough samples
        if len(self.memory) < self.batch_size:
            return None
        
        # Sample batch
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.device)
        
        # Current Q values
        current_q = self.q_network(states).gather(1, actions)
        
        # Target Q values
        with torch.no_grad():
            if self.double_dqn:
                # Double DQN: use online network to select action,
                # target network to evaluate
                next_actions = self.q_network(next_states).argmax(1, keepdim=True)
                next_q = self.target_network(next_states).gather(1, next_actions)
            else:
                next_q = self.target_network(next_states).max(1, keepdim=True)[0]
            
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Compute loss and update
        loss = nn.SmoothL1Loss()(current_q, target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 10.0)
        self.optimizer.step()
        
        # Soft update target network
        self._soft_update()
        
        loss_val = loss.item()
        self.losses.append(loss_val)
        return loss_val
    
    def decay_epsilon(self):
        """Decay exploration rate after each episode."""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
    
    def _soft_update(self):
        """Soft update target network: θ_target = τ*θ_online + (1-τ)*θ_target"""
        for target_param, online_param in zip(
            self.target_network.parameters(), self.q_network.parameters()
        ):
            target_param.data.copy_(
                self.tau * online_param.data + (1 - self.tau) * target_param.data
            )
    
    def save(self, filepath: str):
        """Save model weights."""
        torch.save({
            "q_network": self.q_network.state_dict(),
            "target_network": self.target_network.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "step_count": self.step_count,
        }, filepath)
    
    def load(self, filepath: str):
        """Load model weights."""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.q_network.load_state_dict(checkpoint["q_network"])
        self.target_network.load_state_dict(checkpoint["target_network"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.epsilon = checkpoint["epsilon"]
        self.step_count = checkpoint["step_count"]
