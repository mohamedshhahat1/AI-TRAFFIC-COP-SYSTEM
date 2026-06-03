"""
API Routes for RL Traffic Signal Control.
Integrates into the existing FastAPI backend.

Add to backend/app/main.py:
    from rl_signal_control.integration.api_routes import rl_router
    app.include_router(rl_router, prefix="/api/rl", tags=["RL Signal Control"])
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os

router = APIRouter()

# Global reference to live environment (initialized on startup)
_live_env = None


class RLConfig(BaseModel):
    """Configuration for RL system."""
    agent_type: str = "dqn"
    model_path: Optional[str] = None
    decision_interval: float = 5.0
    control_mode: str = "simulated"


class ManualPhaseRequest(BaseModel):
    """Manual phase override."""
    phase: int


def get_live_env():
    """Get or create the live traffic environment."""
    global _live_env
    if _live_env is None:
        from rl_signal_control.integration.live_environment import LiveTrafficEnv, LiveEnvConfig
        _live_env = LiveTrafficEnv(LiveEnvConfig())
    return _live_env


# ============ STATUS & CONTROL ============

@router.get("/status")
async def get_rl_status():
    """Get full RL system status."""
    env = get_live_env()
    return env.get_status()


@router.post("/start")
async def start_rl_control(config: RLConfig = None):
    """Start RL-based signal control."""
    env = get_live_env()
    
    if config:
        env.config.agent_type = config.agent_type
        env.config.decision_interval = config.decision_interval
        env.config.control_mode = config.control_mode
    
    # Load agent model
    try:
        model_path = config.model_path if config else None
        env.load_agent(
            agent_type=env.config.agent_type,
            model_path=model_path,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load agent: {e}")
    
    env.start()
    return {
        "status": "started",
        "agent_type": env.config.agent_type,
        "decision_interval": env.config.decision_interval,
        "control_mode": env.config.control_mode,
    }


@router.post("/stop")
async def stop_rl_control():
    """Stop RL control (revert to fixed timing)."""
    env = get_live_env()
    env.stop()
    return {"status": "stopped"}


@router.post("/phase")
async def set_manual_phase(request: ManualPhaseRequest):
    """Manually override signal phase (for testing)."""
    env = get_live_env()
    result = env._controller.set_phase(request.phase)
    return result


# ============ METRICS & ANALYTICS ============

@router.get("/metrics")
async def get_rl_metrics():
    """Get current RL performance metrics."""
    env = get_live_env()
    return {
        "controller": env._controller.get_state(),
        "statistics": env._controller.get_statistics(),
        "bridge": env._bridge.get_metrics_summary(),
        "decisions_made": env._decisions_made,
    }


@router.get("/metrics/history")
async def get_metrics_history(last_n: int = 100):
    """Get metrics history for charting."""
    env = get_live_env()
    return {"metrics": env.get_metrics_history(last_n)}


@router.get("/controller/state")
async def get_controller_state():
    """Get current signal controller state."""
    env = get_live_env()
    return env._controller.get_state()


@router.get("/controller/statistics")
async def get_controller_stats():
    """Get signal controller statistics."""
    env = get_live_env()
    return env._controller.get_statistics()


# ============ MODEL MANAGEMENT ============

@router.get("/models")
async def list_available_models():
    """List available trained RL models."""
    models_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "checkpoints"
    )
    
    models = []
    if os.path.exists(models_dir):
        for run_dir in os.listdir(models_dir):
            run_path = os.path.join(models_dir, run_dir)
            if os.path.isdir(run_path):
                best = os.path.exists(os.path.join(run_path, "best_model.pt"))
                final = os.path.exists(os.path.join(run_path, "final_model.pt"))
                models.append({
                    "name": run_dir,
                    "path": run_path,
                    "has_best": best,
                    "has_final": final,
                })
    
    return {"models": models}


@router.post("/models/load")
async def load_model(agent_type: str = "dqn", model_path: str = None):
    """Load a specific trained model."""
    env = get_live_env()
    try:
        env.load_agent(agent_type=agent_type, model_path=model_path)
        return {"status": "loaded", "agent_type": agent_type, "model_path": model_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset")
async def reset_statistics():
    """Reset all RL statistics and counters."""
    env = get_live_env()
    env.reset_statistics()
    return {"status": "reset"}


# Export router for integration
rl_router = router
