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
from loguru import logger
import uvicorn

from .config import settings
from .routes import violations, vehicles, analytics

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

# Routes
app.include_router(violations.router, prefix="/api/violations", tags=["Violations"])
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["Vehicles"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

# WebSocket connections
ws_connections: list = []

# AI Gateway (production integration)
ai_gateway = None


@app.on_event("startup")
async def startup():
    """Initialize AI Gateway and subscribe to Event Bus events."""
    global ai_gateway
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
        loop = asyncio.get_event_loop()

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


@app.get("/", response_class=HTMLResponse)
async def root():
    ai_status = "🟢 Active" if ai_gateway else "🔴 Inactive"
    return f"""
    <html><head><title>AI Traffic Cop API</title></head>
    <body style="font-family:sans-serif;background:#1e1e2e;color:#fff;padding:40px;">
        <h1>🚔 AI Traffic Cop System API</h1>
        <p>Smart Traffic Enforcement & Analytics</p>
        <p><b>AI Gateway:</b> {ai_status}</p>
        <p><b>Architecture:</b> Event-Driven + API Gateway</p>
        <ul>
            <li><a href="/api/docs" style="color:#4285f4;">📖 Swagger Docs</a></li>
            <li><a href="/api/redoc" style="color:#4285f4;">📋 ReDoc</a></li>
            <li><a href="/api/violations" style="color:#4285f4;">🚨 Violations</a></li>
            <li><a href="/api/analytics" style="color:#4285f4;">📊 Analytics</a></li>
            <li><a href="/api/health" style="color:#4285f4;">❤️ Health</a></li>
            <li><a href="/api/analytics/metrics" style="color:#4285f4;">📈 Metrics</a></li>
        </ul>
        <h3>Event-Driven Flow:</h3>
        <pre style="background:#2d2d3f;padding:15px;border-radius:8px;">
AI Engine → Event Bus → Backend (this API)
                     → Alert Service (email/SMS)
                     → Dashboard (WebSocket)
                     → Database (storage)
        </pre>
    </body></html>
    """


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
async def start_camera():
    """Start the AI pipeline camera processing."""
    if not ai_gateway:
        return {"status": "error", "message": "AI Gateway not initialized"}
    return {"status": "started", "message": "Camera feed processing started"}


@app.post("/api/camera/stop")
async def stop_camera():
    """Stop the AI pipeline camera processing."""
    return {"status": "stopped", "message": "Camera feed processing stopped"}


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


def run():
    """Run the server."""
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)


if __name__ == "__main__":
    run()
