# 🚦 RL Traffic Signal Optimization

Adaptive traffic signal control using Deep Reinforcement Learning. An extension of the AI Traffic Cop System that learns optimal signal timing to minimize congestion.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│    SUMO      │────▶│   Gymnasium Env   │────▶│  RL Agent   │
│  Simulator   │◀────│  (TrafficEnv)     │◀────│  (DQN/PPO)  │
└─────────────┘     └──────────────────┘     └─────────────┘
```

## Quick Start

```bash
# Install dependencies
pip install -r rl_signal_control/requirements.txt

# Train DQN on single intersection
python -m rl_signal_control.training.train --agent dqn --network single

# Train PPO on 4x4 grid
python -m rl_signal_control.training.train --agent ppo --network grid_4x4

# Evaluate and compare
python -m rl_signal_control.training.evaluate --compare all

# Launch dashboard
python -m rl_signal_control.dashboard.app
```

## RL Formulation

| Component | Description |
|-----------|-------------|
| **State** | Queue lengths, waiting times, current phase, incoming vehicles |
| **Action** | Select next signal phase (4 phases) |
| **Reward** | Minimize waiting time + maximize throughput - switching penalty |

## Results

| Method | Avg Wait (s) | Throughput (veh/hr) | Improvement |
|--------|:---:|:---:|:---:|
| Fixed-Time | ~45s | ~820 | baseline |
| Actuated | ~38s | ~890 | +14% |
| DQN (ours) | ~28s | ~980 | +37% |
| PPO (ours) | ~26s | ~1010 | +41% |
