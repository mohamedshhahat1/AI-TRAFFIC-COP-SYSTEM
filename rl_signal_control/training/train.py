"""
Training script for RL traffic signal agents.
Supports DQN and PPO with configurable environments.
"""

import argparse
import os
import json
import time
import numpy as np
from datetime import datetime
from typing import Dict, List

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from rl_signal_control.agents.dqn_agent import DQNAgent
from rl_signal_control.agents.ppo_agent import PPOAgent
from rl_signal_control.agents.baselines import FixedTimeAgent, MaxPressureAgent, ActuatedAgent


def create_agent(agent_type: str, state_size: int, action_size: int, config: Dict):
    """Factory function to create agents."""
    if agent_type == "dqn":
        return DQNAgent(
            state_size=state_size,
            action_size=action_size,
            learning_rate=config.get("learning_rate", 1e-3),
            gamma=config.get("gamma", 0.99),
            epsilon_start=config.get("epsilon_start", 1.0),
            epsilon_end=config.get("epsilon_end", 0.01),
            epsilon_decay=config.get("epsilon_decay", 0.995),
            buffer_size=config.get("buffer_size", 100000),
            batch_size=config.get("batch_size", 64),
            double_dqn=config.get("double_dqn", True),
        )
    elif agent_type == "ppo":
        return PPOAgent(
            state_size=state_size,
            action_size=action_size,
            learning_rate=config.get("learning_rate", 3e-4),
            gamma=config.get("gamma", 0.99),
            gae_lambda=config.get("gae_lambda", 0.95),
            clip_epsilon=config.get("clip_epsilon", 0.2),
            n_epochs=config.get("n_epochs", 10),
            batch_size=config.get("batch_size", 64),
            rollout_length=config.get("rollout_length", 2048),
        )
    elif agent_type == "fixed":
        return FixedTimeAgent(num_phases=action_size)
    elif agent_type == "max_pressure":
        return MaxPressureAgent(num_phases=action_size)
    elif agent_type == "actuated":
        return ActuatedAgent(num_phases=action_size)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def train(
    agent_type: str = "dqn",
    network: str = "single",
    num_episodes: int = 500,
    max_steps: int = 3600,
    reward_type: str = "combined",
    save_dir: str = "checkpoints",
    log_interval: int = 10,
    config: Dict = None,
):
    """
    Main training loop.
    
    Args:
        agent_type: 'dqn', 'ppo', 'fixed', 'max_pressure', 'actuated'
        network: 'single' or 'grid_4x4'
        num_episodes: Number of training episodes
        max_steps: Max steps per episode
        reward_type: Reward function type
        save_dir: Directory to save checkpoints
        log_interval: Episodes between logging
        config: Agent hyperparameter overrides
    """
    config = config or {}
    
    # Setup paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    net_dir = os.path.join(base_dir, "configs", "networks")
    
    net_file = os.path.join(net_dir, f"{network}.net.xml")
    route_file = os.path.join(net_dir, f"{network}.rou.xml")
    
    # Create save directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(save_dir, f"{agent_type}_{network}_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    
    print(f"{'='*60}")
    print(f"  RL Traffic Signal Training")
    print(f"{'='*60}")
    print(f"  Agent: {agent_type}")
    print(f"  Network: {network}")
    print(f"  Episodes: {num_episodes}")
    print(f"  Max Steps: {max_steps}")
    print(f"  Reward: {reward_type}")
    print(f"  Save Dir: {run_dir}")
    print(f"{'='*60}\n")
    
    # Create environment
    from rl_signal_control.environment.traffic_env import TrafficSignalEnv
    
    env = TrafficSignalEnv(
        net_file=net_file,
        route_file=route_file,
        delta_time=config.get("delta_time", 5),
        reward_type=reward_type,
        max_steps=max_steps,
        use_gui=config.get("use_gui", False),
    )
    
    # Create agent
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n
    agent = create_agent(agent_type, state_size, action_size, config)
    
    print(f"  State size: {state_size}")
    print(f"  Action size: {action_size}")
    print(f"  Device: {getattr(agent, 'device', 'cpu')}\n")
    
    # Training metrics
    episode_rewards: List[float] = []
    episode_waiting_times: List[float] = []
    episode_throughputs: List[int] = []
    best_reward = -float("inf")
    
    # Training loop
    start_time = time.time()
    
    for episode in range(1, num_episodes + 1):
        state, info = env.reset()
        episode_reward = 0.0
        step = 0
        
        while True:
            # Select action
            action = agent.select_action(state, training=True)
            
            # Step environment
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            # Store transition
            agent.store_transition(state, action, reward, next_state, done)
            
            # Train
            loss = agent.train_step()
            
            episode_reward += reward
            state = next_state
            step += 1
            
            if done:
                break
        
        # Post-episode updates
        if hasattr(agent, "decay_epsilon"):
            agent.decay_epsilon()
        
        # Record metrics
        episode_rewards.append(episode_reward)
        episode_waiting_times.append(info.get("total_waiting_time", 0))
        episode_throughputs.append(info.get("vehicles_passed", 0))
        
        # Save best model
        if episode_reward > best_reward:
            best_reward = episode_reward
            if hasattr(agent, "save"):
                agent.save(os.path.join(run_dir, "best_model.pt"))
        
        # Logging
        if episode % log_interval == 0:
            avg_reward = np.mean(episode_rewards[-log_interval:])
            avg_wait = np.mean(episode_waiting_times[-log_interval:])
            avg_throughput = np.mean(episode_throughputs[-log_interval:])
            elapsed = time.time() - start_time
            
            epsilon_str = f" ε={agent.epsilon:.3f}" if hasattr(agent, "epsilon") else ""
            
            print(
                f"  Episode {episode:4d}/{num_episodes} | "
                f"Reward: {avg_reward:7.2f} | "
                f"Wait: {avg_wait:6.1f}s | "
                f"Throughput: {avg_throughput:5.0f} | "
                f"Time: {elapsed:.0f}s{epsilon_str}"
            )
    
    # Save final model
    if hasattr(agent, "save"):
        agent.save(os.path.join(run_dir, "final_model.pt"))
    
    # Save training history
    history = {
        "agent_type": agent_type,
        "network": network,
        "num_episodes": num_episodes,
        "reward_type": reward_type,
        "config": config,
        "episode_rewards": episode_rewards,
        "episode_waiting_times": episode_waiting_times,
        "episode_throughputs": episode_throughputs,
        "best_reward": best_reward,
        "training_time": time.time() - start_time,
    }
    
    with open(os.path.join(run_dir, "training_history.json"), "w") as f:
        json.dump(history, f, indent=2, default=str)
    
    env.close()
    
    print(f"\n{'='*60}")
    print(f"  Training Complete!")
    print(f"  Best Reward: {best_reward:.2f}")
    print(f"  Final Avg Wait: {np.mean(episode_waiting_times[-20:]):.1f}s")
    print(f"  Final Throughput: {np.mean(episode_throughputs[-20:]):.0f}")
    print(f"  Total Time: {time.time()-start_time:.0f}s")
    print(f"  Saved to: {run_dir}")
    print(f"{'='*60}")
    
    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train RL Traffic Signal Agent")
    parser.add_argument("--agent", type=str, default="dqn", choices=["dqn", "ppo", "fixed", "max_pressure", "actuated"])
    parser.add_argument("--network", type=str, default="single")
    parser.add_argument("--episodes", type=int, default=500)
    parser.add_argument("--max-steps", type=int, default=3600)
    parser.add_argument("--reward", type=str, default="combined")
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--save-dir", type=str, default="checkpoints")
    
    args = parser.parse_args()
    
    config = {}
    if args.lr:
        config["learning_rate"] = args.lr
    if args.gui:
        config["use_gui"] = True
    
    train(
        agent_type=args.agent,
        network=args.network,
        num_episodes=args.episodes,
        max_steps=args.max_steps,
        reward_type=args.reward,
        save_dir=args.save_dir,
        config=config,
    )
