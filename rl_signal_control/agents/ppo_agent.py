"""
Proximal Policy Optimization (PPO) Agent for traffic signal control.
On-policy algorithm with clipped objective for stable training.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
from typing import List, Tuple, Optional


class ActorCritic(nn.Module):
    """
    Shared-backbone Actor-Critic network.
    Actor outputs action probabilities, Critic outputs state value.
    
    Architecture:
        Shared: Input → 128 → 128
        Actor head: 128 → 64 → num_actions (softmax)
        Critic head: 128 → 64 → 1
    """
    
    def __init__(self, state_size: int, action_size: int):
        super().__init__()
        
        # Shared feature extractor
        self.shared = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.LayerNorm(128),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.LayerNorm(128),
        )
        
        # Actor head (policy)
        self.actor = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_size),
            nn.Softmax(dim=-1),
        )
        
        # Critic head (value function)
        self.critic = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )
    
    def forward(self, state):
        features = self.shared(state)
        action_probs = self.actor(features)
        value = self.critic(features)
        return action_probs, value
    
    def get_action(self, state):
        """Sample action from policy distribution."""
        action_probs, value = self.forward(state)
        dist = Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        return action.item(), log_prob, value
    
    def evaluate(self, states, actions):
        """Evaluate actions for PPO update."""
        action_probs, values = self.forward(states)
        dist = Categorical(action_probs)
        log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        return log_probs, values.squeeze(-1), entropy


class RolloutBuffer:
    """Stores trajectories for on-policy training."""
    
    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []
    
    def store(self, state, action, reward, log_prob, value, done):
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.log_probs.append(log_prob)
        self.values.append(value)
        self.dones.append(done)
    
    def clear(self):
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.log_probs.clear()
        self.values.clear()
        self.dones.clear()
    
    def __len__(self):
        return len(self.states)


class PPOAgent:
    """
    PPO Agent with:
    - Clipped surrogate objective
    - Generalized Advantage Estimation (GAE)
    - Value function clipping
    - Entropy bonus for exploration
    - Mini-batch updates over multiple epochs
    """
    
    def __init__(
        self,
        state_size: int,
        action_size: int,
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
        max_grad_norm: float = 0.5,
        n_epochs: int = 10,
        batch_size: int = 64,
        rollout_length: int = 2048,
        device: Optional[str] = None,
    ):
        """
        Initialize PPO Agent.
        
        Args:
            state_size: Dimension of state space
            action_size: Number of discrete actions
            learning_rate: Learning rate
            gamma: Discount factor
            gae_lambda: GAE lambda for advantage estimation
            clip_epsilon: PPO clipping parameter
            value_coef: Value loss coefficient
            entropy_coef: Entropy bonus coefficient
            max_grad_norm: Maximum gradient norm for clipping
            n_epochs: Number of SGD epochs per rollout
            batch_size: Mini-batch size
            rollout_length: Steps to collect before updating
            device: 'cuda' or 'cpu'
        """
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.rollout_length = rollout_length
        
        # Device
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Network
        self.policy = ActorCritic(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=learning_rate, eps=1e-5)
        
        # Rollout buffer
        self.buffer = RolloutBuffer()
        
        # Training stats
        self.losses = []
        self.policy_losses = []
        self.value_losses = []
        self.entropy_values = []
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        Select action from policy.
        
        Args:
            state: Current observation
            training: If True, sample from distribution; if False, take argmax
            
        Returns:
            Selected action index
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action_probs, value = self.policy(state_tensor)
        
        if training:
            dist = Categorical(action_probs)
            action = dist.sample()
            log_prob = dist.log_prob(action)
            
            # Store for later update
            self._last_log_prob = log_prob.item()
            self._last_value = value.item()
            
            return action.item()
        else:
            return action_probs.argmax(dim=-1).item()
    
    def store_transition(
        self, state: np.ndarray, action: int, reward: float,
        next_state: np.ndarray, done: bool
    ):
        """Store transition in rollout buffer."""
        self.buffer.store(
            state, action, reward,
            self._last_log_prob, self._last_value, done
        )
    
    def should_update(self) -> bool:
        """Check if enough transitions collected for update."""
        return len(self.buffer) >= self.rollout_length
    
    def train_step(self) -> Optional[float]:
        """
        Perform PPO update using collected rollout.
        
        Returns:
            Average loss or None if buffer not full
        """
        if not self.should_update():
            return None
        
        # Compute returns and advantages using GAE
        advantages, returns = self._compute_gae()
        
        # Convert to tensors
        states = torch.FloatTensor(np.array(self.buffer.states)).to(self.device)
        actions = torch.LongTensor(self.buffer.actions).to(self.device)
        old_log_probs = torch.FloatTensor(self.buffer.log_probs).to(self.device)
        advantages_tensor = torch.FloatTensor(advantages).to(self.device)
        returns_tensor = torch.FloatTensor(returns).to(self.device)
        
        # Normalize advantages
        advantages_tensor = (advantages_tensor - advantages_tensor.mean()) / (
            advantages_tensor.std() + 1e-8
        )
        
        # Multiple epochs of SGD
        total_loss = 0.0
        num_updates = 0
        
        for _ in range(self.n_epochs):
            # Random mini-batches
            indices = np.arange(len(self.buffer))
            np.random.shuffle(indices)
            
            for start in range(0, len(indices), self.batch_size):
                end = start + self.batch_size
                batch_idx = indices[start:end]
                
                # Get batch
                batch_states = states[batch_idx]
                batch_actions = actions[batch_idx]
                batch_old_log_probs = old_log_probs[batch_idx]
                batch_advantages = advantages_tensor[batch_idx]
                batch_returns = returns_tensor[batch_idx]
                
                # Evaluate current policy on batch
                new_log_probs, values, entropy = self.policy.evaluate(
                    batch_states, batch_actions
                )
                
                # Policy loss (clipped surrogate)
                ratio = torch.exp(new_log_probs - batch_old_log_probs)
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(
                    ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon
                ) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                # Value loss
                value_loss = nn.MSELoss()(values, batch_returns)
                
                # Entropy bonus
                entropy_loss = -entropy.mean()
                
                # Total loss
                loss = (
                    policy_loss
                    + self.value_coef * value_loss
                    + self.entropy_coef * entropy_loss
                )
                
                # Update
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    self.policy.parameters(), self.max_grad_norm
                )
                self.optimizer.step()
                
                total_loss += loss.item()
                num_updates += 1
        
        # Clear buffer after update
        self.buffer.clear()
        
        avg_loss = total_loss / max(num_updates, 1)
        self.losses.append(avg_loss)
        return avg_loss
    
    def _compute_gae(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute Generalized Advantage Estimation.
        
        GAE(γ,λ) = Σ (γλ)^t * δ_t
        where δ_t = r_t + γ*V(s_{t+1}) - V(s_t)
        """
        rewards = np.array(self.buffer.rewards)
        values = np.array(self.buffer.values)
        dones = np.array(self.buffer.dones)
        
        advantages = np.zeros_like(rewards)
        last_gae = 0
        
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0  # Terminal
            else:
                next_value = values[t + 1]
            
            # TD error
            delta = rewards[t] + self.gamma * next_value * (1 - dones[t]) - values[t]
            
            # GAE
            last_gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * last_gae
            advantages[t] = last_gae
        
        returns = advantages + values
        return advantages, returns
    
    def save(self, filepath: str):
        """Save model weights."""
        torch.save({
            "policy": self.policy.state_dict(),
            "optimizer": self.optimizer.state_dict(),
        }, filepath)
    
    def load(self, filepath: str):
        """Load model weights."""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.policy.load_state_dict(checkpoint["policy"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
