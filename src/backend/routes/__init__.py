"""API Routes."""
from .violations import router as violations_router
from .vehicles import router as vehicles_router
from .statistics import router as statistics_router
from .camera import router as camera_router

__all__ = ["violations_router", "vehicles_router", "statistics_router", "camera_router"]
