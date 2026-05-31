"""
FastAPI Main Application
Entry point for the AI Traffic Cop System backend.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from loguru import logger
import uvicorn

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


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html><head><title>AI Traffic Cop API</title></head>
    <body style="font-family:sans-serif;background:#1e1e2e;color:#fff;padding:40px;">
        <h1>🚔 AI Traffic Cop System API</h1>
        <p>Smart Traffic Enforcement & Analytics</p>
        <ul>
            <li><a href="/api/docs" style="color:#4285f4;">📖 Swagger Docs</a></li>
            <li><a href="/api/redoc" style="color:#4285f4;">📋 ReDoc</a></li>
            <li><a href="/api/violations" style="color:#4285f4;">🚨 Violations</a></li>
            <li><a href="/api/analytics" style="color:#4285f4;">📊 Analytics</a></li>
        </ul>
    </body></html>
    """


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.VERSION}


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """Live violation/tracking data stream."""
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
    """Broadcast to all WebSocket clients."""
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
