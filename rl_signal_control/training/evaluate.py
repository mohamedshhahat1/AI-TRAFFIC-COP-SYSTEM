"""
Evaluation and comparison script.
Runs all agents on same scenarios and generates comparison plots.
"""

import argparse
import os
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def evaluate_agent(agent, env, num_episodes: int = 10) -> Dict:
    """
    Evaluate an agent over multiple episodes.
    
    Returns:
        Dict with avg metrics: waiting_time, throughput, queue_length
    """
    metrics = {
        "episode_rewards": [],
        "avg_waiting_times": [],
        "throughputs": [],
        "avg_queue_lengths": [],
    }
    
    for ep in range(num_episodes):
        state, info = env.reset(seed=ep)
        episode_reward = 0.0
        total_wait = 0.0
        total_queue = 0.0
        steps = 0
        
        while True:
            action = agent.select_action(state, training=False)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            episode_reward += reward
            total_wait += info.get("total_waiting_time", 0)
            total_queue += info.get("total_queue_length", 0)
            steps += 1
            state = next_state
            
            if done:
                break
        
        metrics["episode_rewards"].append(episode_reward)
        metrics["avg_waiting_times"].append(total_wait / max(steps, 1))
        metrics["throughputs"].append(info.get("vehicles_passed", 0))
        metrics["avg_queue_lengths"].append(total_queue / max(steps, 1))
    
    return {
        "avg_reward": np.mean(metrics["episode_rewards"]),
        "std_reward": np.std(metrics["episode_rewards"]),
        "avg_waiting_time": np.mean(metrics["avg_waiting_times"]),
        "avg_throughput": np.mean(metrics["throughputs"]),
        "avg_queue_length": np.mean(metrics["avg_queue_lengths"]),
        "raw": metrics,
    }


def plot_comparison(results: Dict[str, Dict], save_path: str = "comparison.png"):
    """Generate comparison bar charts."""
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    agents = list(results.keys())
    colors = sns.color_palette("husl", len(agents))
    
    # Plot 1: Average Waiting Time
    wait_times = [results[a]["avg_waiting_time"] for a in agents]
    axes[0].bar(agents, wait_times, color=colors)
    axes[0].set_title("Average Waiting Time (s)", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Seconds")
    axes[0].tick_params(axis="x", rotation=45)
    
    # Plot 2: Throughput
    throughputs = [results[a]["avg_throughput"] for a in agents]
    axes[1].bar(agents, throughputs, color=colors)
    axes[1].set_title("Throughput (vehicles/episode)", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Vehicles")
    axes[1].tick_params(axis="x", rotation=45)
    
    # Plot 3: Average Queue Length
    queues = [results[a]["avg_queue_length"] for a in agents]
    axes[2].bar(agents, queues, color=colors)
    axes[2].set_title("Average Queue Length", fontsize=12, fontweight="bold")
    axes[2].set_ylabel("Vehicles")
    axes[2].tick_params(axis="x", rotation=45)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Comparison plot saved: {save_path}")


def plot_training_curves(history_files: List[str], save_path: str = "training_curves.png"):
    """Plot training reward curves for multiple agents."""
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    for filepath in history_files:
        with open(filepath) as f:
            history = json.load(f)
        
        label = history["agent_type"].upper()
        rewards = history["episode_rewards"]
        waits = history["episode_waiting_times"]
        
        # Smooth with moving average
        window = 20
        smoothed_rewards = np.convolve(rewards, np.ones(window)/window, mode="valid")
        smoothed_waits = np.convolve(waits, np.ones(window)/window, mode="valid")
        
        axes[0].plot(smoothed_rewards, label=label)
        axes[1].plot(smoothed_waits, label=label)
    
    axes[0].set_title("Episode Reward (smoothed)", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Episode")
    axes[0].set_ylabel("Reward")
    axes[0].legend()
    
    axes[1].set_title("Total Waiting Time (smoothed)", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Episode")
    axes[1].set_ylabel("Waiting Time (s)")
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Training curves saved: {save_path}")


def print_comparison_table(results: Dict[str, Dict]):
    """Print formatted comparison table."""
    print(f"\n{'='*70}")
    print(f"{'Agent':<15} {'Avg Wait (s)':<15} {'Throughput':<15} {'Queue Len':<15} {'Reward':<10}")
    print(f"{'-'*70}")
    
    # Sort by waiting time (lower is better)
    sorted_agents = sorted(results.keys(), key=lambda a: results[a]["avg_waiting_time"])
    
    baseline_wait = results.get("Fixed-Time", {}).get("avg_waiting_time", 1)
    
    for agent in sorted_agents:
        r = results[agent]
        improvement = ((baseline_wait - r["avg_waiting_time"]) / baseline_wait * 100) if baseline_wait > 0 else 0
        print(
            f"{agent:<15} {r['avg_waiting_time']:<15.1f} "
            f"{r['avg_throughput']:<15.0f} {r['avg_queue_length']:<15.1f} "
            f"{r['avg_reward']:<10.2f}"
        )
    
    print(f"{'='*70}")
    
    # Show improvements
    if "Fixed-Time" in results:
        print(f"\nImprovement over Fixed-Time baseline:")
        for agent in sorted_agents:
            if agent != "Fixed-Time":
                improvement = (
                    (baseline_wait - results[agent]["avg_waiting_time"]) / baseline_wait * 100
                )
                print(f"  {agent}: {improvement:+.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate RL Traffic Signal Agents")
    parser.add_argument("--compare", type=str, default="all",
                       help="Agents to compare: 'all' or comma-separated list")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--network", type=str, default="single")
    parser.add_argument("--save-dir", type=str, default="experiments/results")
    
    args = parser.parse_args()
    
    print(f"  Evaluation will run {args.episodes} episodes per agent")
    print(f"  Network: {args.network}")
    print(f"  Results: {args.save_dir}")
