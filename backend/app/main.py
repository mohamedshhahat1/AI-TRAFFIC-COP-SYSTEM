"""
FastAPI Main Application
Entry point for the AI Traffic Cop System backend.

Fully integrated with:
- AIGateway (single interface to AI Engine)
- Event Bus (real-time violation/tracking events)
- WebSocket broadcasting (dashboard live updates)
- Monitoring (health, metrics, logs)
"""

import sys
import os
import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("main")
except ImportError:
    from loguru import logger
import uvicorn

from .config import settings
from .routes import violations, vehicles, analytics
from .video_processor import VideoProcessor

# Add project root to path for ai_engine imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Create app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Smart Traffic Enforcement & Analytics REST API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React frontend static files (single port deployment)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

_frontend_build = Path(__file__).resolve().parents[2] / "frontend" / "build"
if _frontend_build.exists():
    app.mount("/static", StaticFiles(directory=str(_frontend_build / "static")), name="static")

# Routes
app.include_router(violations.router, prefix="/api/violations", tags=["Violations"])
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["Vehicles"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

# WebSocket connections
ws_connections: list = []

# AI Gateway (production integration)
ai_gateway = None
video_processor = None


@app.on_event("startup")
async def startup():
    """Initialize AI Gateway and subscribe to Event Bus events."""
    global ai_gateway, video_processor
    logger.info("🚀 Starting AI Traffic Cop API...")

    # Initialize AI Gateway
    try:
        from ai_engine.api_bridge import AIGateway

        # Load config
        config = {}
        config_path = Path(__file__).resolve().parents[3] / "configs" / "settings.yaml"
        if config_path.exists():
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}

        ai_gateway = AIGateway(config)
        ai_gateway.start()

        # Subscribe to Event Bus → broadcast to WebSocket clients
        # Use call_soon_threadsafe since Event Bus may fire from non-asyncio threads
        loop = asyncio.get_running_loop()

        ai_gateway.on_violation(
            lambda v: loop.call_soon_threadsafe(asyncio.ensure_future, broadcast({"type": "violation", "data": v}))
        )
        ai_gateway.on_accident_risk(
            lambda r: loop.call_soon_threadsafe(asyncio.ensure_future, broadcast({"type": "accident_risk", "data": r}))
        )
        ai_gateway.on_congestion_change(
            lambda c: loop.call_soon_threadsafe(asyncio.ensure_future, broadcast({"type": "congestion", "data": c}))
        )

        # Subscribe to tracking updates via Event Bus
        event_bus = ai_gateway.event_bus
        if event_bus:
            event_bus.on("tracking.update", lambda event: loop.call_soon_threadsafe(
                asyncio.ensure_future, broadcast({"type": "tracking", "data": event.data})
            ))

        # Initialize video processor (connects pipeline → WebSocket)
        video_processor = VideoProcessor(ai_gateway, broadcast)
        
        logger.info("✅ AI Gateway initialized - Event Bus subscriptions active")

    except ImportError as e:
        logger.warning(f"⚠️ AI Engine not available: {e}")
        logger.info("Running in API-only mode (no AI processing)")
    except Exception as e:
        logger.error(f"❌ AI Gateway init failed: {e}")
        logger.info("Running in API-only mode (AI Gateway disabled)")

    logger.info("✅ API server ready")


@app.on_event("shutdown")
async def shutdown():
    """Graceful shutdown - stop AI Gateway."""
    global ai_gateway
    if ai_gateway:
        ai_gateway.stop()
        logger.info("AI Gateway stopped")
    logger.info("🛑 API server stopped")


@app.get("/")
async def root():
    """Serve React dashboard (single-port deployment)."""
    index_path = _frontend_build / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>Frontend not built. Run: cd frontend && npm run build</h1>")


@app.get("/api/health")
async def health():
    """Health check with full AI Gateway + Event Bus status."""
    gateway_health = ai_gateway.health() if ai_gateway else {"status": "not_initialized"}
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "ai_gateway": gateway_health,
        "websocket_clients": len(ws_connections),
    }


@app.get("/api/events/metrics")
async def event_metrics():
    """Get Event Bus metrics (emitted, handled, failed, success rate)."""
    if ai_gateway:
        return ai_gateway.event_bus.get_metrics()
    return {"status": "ai_gateway_not_initialized", "total_emitted": 0}


@app.get("/api/events/history")
async def event_history(topic: str = "violation.*", limit: int = 20):
    """Get recent events from the Event Bus."""
    if ai_gateway:
        return {"events": ai_gateway.event_bus.get_history(topic, limit)}
    return {"events": []}


@app.post("/api/camera/start")
async def start_camera(source: str = "data/videos/traffic.mp4"):
    """Start processing video - results stream to WebSocket."""
    global video_processor
    if not ai_gateway:
        return {"status": "error", "message": "AI Gateway not initialized"}
    if not video_processor:
        return {"status": "error", "message": "Video processor not available"}
    return video_processor.start(source)


@app.post("/api/camera/stop")
async def stop_camera():
    """Stop video processing."""
    global video_processor
    if video_processor:
        return video_processor.stop()
    return {"status": "stopped"}


@app.get("/api/camera/stats")
async def camera_stats():
    """Get live processing stats (FPS, objects, violations)."""
    if video_processor and video_processor.is_running:
        return {"running": True, **video_processor.stats}
    return {"running": False, "fps": 0, "objects": 0, "tracks": 0, "frame": 0}


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    Live event stream via WebSocket.
    Dashboard/mobile connects here to receive real-time:
    - Violation alerts
    - Tracking updates
    - Congestion changes
    - Accident risk warnings
    """
    await websocket.accept()
    ws_connections.append(websocket)
    logger.info(f"🔌 WS connected ({len(ws_connections)} active)")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"status": "ok", "echo": data})
    except WebSocketDisconnect:
        try:
            ws_connections.remove(websocket)
        except ValueError:
            pass  # Already removed by broadcast() cleanup
        logger.info(f"WS disconnected ({len(ws_connections)} active)")


async def broadcast(data: dict):
    """Broadcast event to ALL connected WebSocket clients (dashboard + mobile)."""
    disconnected = []
    for ws in list(ws_connections):  # Iterate over copy to avoid concurrent modification
        try:
            await ws.send_json(data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        try:
            ws_connections.remove(ws)
        except ValueError:
            pass


# Catch-all: serve React frontend for any non-API route (SPA routing)
@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve React app for all non-API routes (SPA client-side routing)."""
    # Check if it's a static file
    file_path = _frontend_build / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    # Otherwise serve index.html (React handles routing)
    index_path = _frontend_build / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "Frontend not built. Run: cd frontend && npm run build"}


def run():
    """Run the server."""
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)


if __name__ == "__main__":
    run()
