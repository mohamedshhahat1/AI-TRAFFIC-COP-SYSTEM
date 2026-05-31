"""
FastAPI Main Application
Entry point for the AI Traffic Cop System backend.

Integration:
    - Uses AIGateway as the single interface to the AI Engine
    - Subscribes to Event Bus for real-time violation/tracking events
    - Broadcasts events to WebSocket clients (dashboard)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from loguru import logger
import uvicorn
import asyncio

from .config import settings
from .routes import violations, vehicles, analytics

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

# AI Gateway reference (initialized on startup)
ai_gateway = None


@app.on_event("startup")
async def startup():
    """Initialize AI Gateway and subscribe to events."""
    global ai_gateway
    logger.info("🚀 Starting AI Traffic Cop API...")
    
    # In production, initialize the AI Gateway here:
    # from ai_engine.api_bridge import AIGateway
    # ai_gateway = AIGateway(config)
    # ai_gateway.start()
    #
    # Subscribe to events for WebSocket broadcasting:
    # ai_gateway.on_violation(lambda v: asyncio.create_task(broadcast({"type": "violation", "data": v})))
    # ai_gateway.on_accident_risk(lambda r: asyncio.create_task(broadcast({"type": "accident_risk", "data": r})))
    # ai_gateway.on_congestion_change(lambda c: asyncio.create_task(broadcast({"type": "congestion", "data": c})))
    
    logger.info("✅ API server ready")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    global ai_gateway
    if ai_gateway:
        ai_gateway.stop()
    logger.info("🛑 API server stopped")


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html><head><title>AI Traffic Cop API</title></head>
    <body style="font-family:sans-serif;background:#1e1e2e;color:#fff;padding:40px;">
        <h1>🚔 AI Traffic Cop System API</h1>
        <p>Smart Traffic Enforcement & Analytics</p>
        <p><b>Architecture:</b> Event-Driven + API Gateway</p>
        <ul>
            <li><a href="/api/docs" style="color:#4285f4;">📖 Swagger Docs</a></li>
            <li><a href="/api/redoc" style="color:#4285f4;">📋 ReDoc</a></li>
            <li><a href="/api/violations" style="color:#4285f4;">🚨 Violations</a></li>
            <li><a href="/api/analytics" style="color:#4285f4;">📊 Analytics</a></li>
            <li><a href="/api/health" style="color:#4285f4;">❤️ Health</a></li>
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
    """Health check with AI Gateway status."""
    gateway_health = ai_gateway.health() if ai_gateway else {"status": "not_initialized"}
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "ai_gateway": gateway_health,
    }


@app.get("/api/events/metrics")
async def event_metrics():
    """Get Event Bus metrics."""
    if ai_gateway:
        return ai_gateway.event_bus.get_metrics() if hasattr(ai_gateway, 'event_bus') else {}
    return {"status": "ai_gateway_not_initialized"}


@app.get("/api/events/history")
async def event_history(topic: str = "violation.*", limit: int = 20):
    """Get recent events from the Event Bus."""
    if ai_gateway and hasattr(ai_gateway, 'get_event_history'):
        return {"events": ai_gateway.get_event_history(topic, limit)}
    return {"events": []}


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    Live event stream via WebSocket.
    Dashboard connects here to receive real-time:
    - Violation alerts
    - Tracking updates
    - Congestion changes
    - Accident risk warnings
    """
    await websocket.accept()
    ws_connections.append(websocket)
    logger.info(f"WS connected ({len(ws_connections)} active)")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"status": "ok", "echo": data})
    except WebSocketDisconnect:
        ws_connections.remove(websocket)
        logger.info(f"WS disconnected ({len(ws_connections)} active)")


async def broadcast(data: dict):
    """Broadcast event to all WebSocket clients."""
    for ws in ws_connections[:]:
        try:
            await ws.send_json(data)
        except Exception:
            ws_connections.remove(ws)


def run():
    """Run the server."""
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)


if __name__ == "__main__":
    run()
