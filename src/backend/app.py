"""
FastAPI Application
Main backend server for the AI Traffic Cop System.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from loguru import logger
import uvicorn
import json
import asyncio
from pathlib import Path

from .routes import violations_router, vehicles_router, statistics_router, camera_router
from .database.db import init_database, get_db

# Create FastAPI app
app = FastAPI(
    title="AI Traffic Cop System API",
    description="Smart Traffic Enforcement & Analytics System REST API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(violations_router, prefix="/api/violations", tags=["Violations"])
app.include_router(vehicles_router, prefix="/api/vehicles", tags=["Vehicles"])
app.include_router(statistics_router, prefix="/api/statistics", tags=["Statistics"])
app.include_router(camera_router, prefix="/api/camera", tags=["Camera"])

# WebSocket connections
active_connections: list = []


@app.on_event("startup")
async def startup():
    """Initialize database and services on startup."""
    logger.info("🚀 AI Traffic Cop System API starting...")
    await init_database()
    logger.info("✅ API server ready")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("🛑 API server shutting down...")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - API info."""
    return """
    <html>
        <head><title>AI Traffic Cop System</title></head>
        <body>
            <h1>🚔 AI Traffic Cop System API</h1>
            <p>Smart Traffic Enforcement & Analytics System</p>
            <ul>
                <li><a href="/api/docs">📖 API Documentation (Swagger)</a></li>
                <li><a href="/api/redoc">📋 API Documentation (ReDoc)</a></li>
                <li><a href="/api/violations">🚨 Violations</a></li>
                <li><a href="/api/statistics">📊 Statistics</a></li>
            </ul>
        </body>
    </html>
    """


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Traffic Cop System",
        "version": "1.0.0",
    }


@app.websocket("/ws/live-feed")
async def websocket_live_feed(websocket: WebSocket):
    """WebSocket endpoint for live violation feed."""
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket connected. Active: {len(active_connections)}")
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_json({"status": "connected", "message": data})
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active: {len(active_connections)}")


async def broadcast_violation(violation_data: dict):
    """Broadcast violation to all connected WebSocket clients."""
    for connection in active_connections:
        try:
            await connection.send_json(violation_data)
        except Exception:
            active_connections.remove(connection)


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    uvicorn.run(
        "src.backend.app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
