"""
Rate Limiting Middleware
Prevents API abuse with per-IP rate limiting.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter per IP."""

    def __init__(self, app, requests_per_minute: int = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self._requests: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health check
        if request.url.path in ("/api/health", "/", "/api/docs", "/api/redoc"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60  # 1-minute window

        # Clean old entries
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        # Check rate limit
        if len(self._requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Try again later.",
                    "retry_after_seconds": 60,
                },
                headers={"Retry-After": "60"},
            )

        # Record this request
        self._requests[client_ip].append(now)

        # Periodically clean up old IPs (every 1000 requests across all IPs)
        total = sum(len(v) for v in self._requests.values())
        if total > 10000:
            stale_ips = [
                ip for ip, times in self._requests.items()
                if not times or times[-1] < window_start
            ]
            for ip in stale_ips:
                del self._requests[ip]

        return await call_next(request)
