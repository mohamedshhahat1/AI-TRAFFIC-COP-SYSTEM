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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("main")
except ImportError:
    from loguru import logger
import uvicorn

from .config import settings
from .routes import violations, vehicles, analytics
from .routes import plates
from .video_processor import VideoProcessor
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.auth import api_key_auth

# Add project root to path for ai_engine and rl_signal_control imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Create app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Smart Traffic Enforcement & Analytics REST API",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    redirect_slashes=False,
)

# API request counter
_api_request_count = 0

@app.middleware("http")
async def count_requests(request, call_next):
    global _api_request_count
    _api_request_count += 1
    response = await call_next(request)
    return response

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True if "*" not in settings.CORS_ORIGINS else False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Routes
app.include_router(violations.router, prefix="/api/violations", tags=["Violations"])
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["Vehicles"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(plates.router, prefix="/api/plates", tags=["License Plates"])

# RL Signal Control Routes
try:
    from rl_signal_control.integration.api_routes import rl_router
    app.include_router(rl_router, prefix="/api/rl", tags=["RL Signal Control"])
    logger.info("✅ RL Signal Control routes registered at /api/rl")
except ImportError:
    logger.info("ℹ️ RL Signal Control module not available (optional)")

# WebSocket connections
ws_connections: list = []

# AI Gateway (production integration)
ai_gateway = None
video_processor = None


@app.on_event("startup")
async def startup():
    """Initialize database and AI Gateway, subscribe to Event Bus events."""
    global ai_gateway, video_processor
    logger.info("🚀 Starting AI Traffic Cop API...")

    # Initialize database
    from .services.db_service import init_db
    await init_db()
    logger.info("✅ Database initialized")

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

    # Initialize RL Signal Control integration
    try:
        from rl_signal_control.integration.plug_into_backend import setup_rl_integration
        setup_rl_integration(app, ai_gateway, broadcast)
        logger.info("✅ RL Signal Control integrated")
    except ImportError:
        logger.info("ℹ️ RL Signal Control not available (install rl_signal_control)")
    except Exception as e:
        logger.warning(f"⚠️ RL integration failed: {e}")

    logger.info("✅ API server ready")


@app.on_event("shutdown")
async def shutdown():
    """Graceful shutdown - stop AI Gateway."""
    global ai_gateway
    if ai_gateway:
        ai_gateway.stop()
        logger.info("AI Gateway stopped")
    logger.info("🛑 API server stopped")


@app.get("/", response_class=HTMLResponse)
async def root():
    """API info page."""
    ai_status = "🟢 Active" if ai_gateway else "🔴 Inactive"
    return f"""
    <html><head><title>AI Traffic Cop API</title></head>
    <body style="font-family:sans-serif;background:#1e1e2e;color:#fff;padding:40px;">
        <h1>🚔 AI Traffic Cop System API</h1>
        <p>AI Gateway: {ai_status}</p>
        <ul>
            <li><a href="/api/docs" style="color:#4285f4;">📖 API Docs</a></li>
            <li><a href="/api/health" style="color:#4285f4;">❤️ Health</a></li>
        </ul>
        <p>Frontend: <a href="http://localhost:3000" style="color:#4285f4;">http://localhost:3000</a></p>
    </body></html>
    """


@app.get("/api/stats/requests")
async def api_request_count():
    """Get total API requests served."""
    return {"total_requests": _api_request_count}


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
async def start_camera(source: str = "data/videos/traffic.mp4", _user: str = Depends(api_key_auth)):
    """Start processing video - results stream to WebSocket."""
    global video_processor
    if not ai_gateway:
        return {"status": "error", "message": "AI Gateway not initialized"}
    if not video_processor:
        return {"status": "error", "message": "Video processor not available"}

    # Validate source: only allow local files in data/ or RTSP streams
    import re
    if source.startswith("rtsp://") or source.startswith("http://") or source.startswith("https://"):
        pass  # Allow streaming URLs
    else:
        # Local file: must be within data/ directory, no path traversal
        from pathlib import Path
        safe_path = Path(source).resolve()
        allowed_dir = Path("data").resolve()
        if ".." in source or not str(safe_path).startswith(str(allowed_dir)):
            return {"status": "error", "message": "Invalid source path. Files must be in data/ directory."}

    return video_processor.start(source)


@app.post("/api/camera/stop")
async def stop_camera(_user: str = Depends(api_key_auth)):
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


@app.get("/api/camera/info")
async def camera_info():
    """Get camera source information (resolution, FPS, status)."""
    if video_processor:
        return video_processor.camera_info
    return {"source": "", "name": "No camera", "resolution": "—", "fps": 0, "status": "Disconnected"}


@app.get("/api/camera/feed")
async def video_feed():
    """MJPEG video stream with annotated frames (bounding boxes, IDs, speed)."""
    import time
    
    BOUNDARY = b"--frame"
    CRLF = b"\r\n"
    CONTENT_TYPE = b"Content-Type: image/jpeg"
    
    def generate():
        while True:
            if video_processor and video_processor._latest_frame:
                frame = video_processor._latest_frame
                yield BOUNDARY + CRLF + CONTENT_TYPE + CRLF + CRLF + frame + CRLF
            time.sleep(0.1)
    
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.post("/api/camera/upload")
async def upload_video(file: UploadFile = File(...), _user: str = Depends(api_key_auth)):
    """Upload a traffic video for AI processing."""
    from pathlib import Path
    import shutil
    import re

    # Validate file type
    ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

    if not file.filename:
        return {"status": "error", "message": "No filename provided"}

    # Sanitize filename - remove path separators and dangerous characters
    safe_filename = re.sub(r'[^\w\-.]', '_', Path(file.filename).name)
    ext = Path(safe_filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        return {"status": "error", "message": f"Invalid file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"}

    # Save uploaded file
    upload_dir = Path("data/videos")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / safe_filename

    # Ensure the resolved path is within the upload directory
    if not str(file_path.resolve()).startswith(str(upload_dir.resolve())):
        return {"status": "error", "message": "Invalid filename"}

    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return {"status": "error", "message": f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"}

    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "status": "uploaded",
        "filename": safe_filename,
        "path": str(file_path),
        "message": f"Video uploaded. Start processing with POST /api/camera/start?source={file_path}"
    }



@app.get("/api/cameras")
async def list_cameras():
    """List all cameras in the network with live status."""
    import yaml
    from pathlib import Path
    
    cameras = []
    config_path = Path(__file__).resolve().parents[2] / "configs" / "camera_config.yaml"
    
    if config_path.exists():
        with open(config_path) as f:
            cam_config = yaml.safe_load(f)
        
        for cam in cam_config.get("cameras", []):
            # First camera is active (connected to video processor)
            is_first = cam.get("id") == cam_config["cameras"][0]["id"]
            is_active = video_processor and video_processor.is_running if is_first else False
            
            stats = video_processor.stats if (is_first and video_processor and video_processor.is_running) else {}
            
            cameras.append({
                "id": cam.get("id", "unknown"),
                "location": cam.get("location", "Unknown"),
                "status": "active" if is_active else ("standby" if not is_first else "offline"),
                "vehicles": stats.get("tracks", 0) if is_active else 0,
                "congestion": stats.get("congestion", "free") if is_active else "unknown",
                "fps": stats.get("fps", 0) if is_active else 0,
                "coordinates": cam.get("coordinates", [0, 0]),
            })
    
    # Add simulated cameras for demo if only 3 in config
    if len(cameras) < 4:
        cameras.append({
            "id": "cam_04",
            "location": "Downtown Ring Road",
            "status": "standby",
            "vehicles": 0,
            "congestion": "unknown",
            "fps": 0,
            "coordinates": [30.05, 31.24],
        })
    
    return {"cameras": cameras, "total": len(cameras), "active": sum(1 for c in cameras if c["status"] == "active")}

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    Live event stream via WebSocket.
    Dashboard/mobile connects here to receive real-time:
    - Violation alerts
    - Tracking updates
    - Congestion changes
    - Accident risk warnings

    Optional token parameter for authentication when API_KEY is set.
    Connect with: ws://host/ws/live?token=YOUR_API_KEY
    """
    # Validate token if API_KEY is configured
    if settings.API_KEY:
        if not token or token != settings.API_KEY:
            await websocket.close(code=4001, reason="Invalid or missing token")
            return

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


def run():
    """Run the server."""
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)


if __name__ == "__main__":
    run()
