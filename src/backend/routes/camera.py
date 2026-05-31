"""
Camera API Routes
Camera feed control endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter()

# Camera state (in-memory for now)
camera_state = {
    "is_running": False,
    "source": None,
    "fps": 0,
    "resolution": None,
}


@router.get("/status")
async def camera_status():
    """Get camera feed status."""
    return camera_state


@router.post("/start")
async def start_camera(source: Optional[str] = "0"):
    """Start camera feed processing."""
    camera_state["is_running"] = True
    camera_state["source"] = source
    
    return {
        "status": "started",
        "source": source,
        "message": "Camera feed processing started"
    }


@router.post("/stop")
async def stop_camera():
    """Stop camera feed processing."""
    camera_state["is_running"] = False
    
    return {
        "status": "stopped",
        "message": "Camera feed processing stopped"
    }


@router.get("/info")
async def camera_info():
    """Get camera information."""
    return {
        "supported_sources": [
            "Local video files (.mp4, .avi)",
            "RTSP streams (rtsp://...)",
            "USB webcam (device index: 0, 1, ...)",
        ],
        "current_state": camera_state,
    }
