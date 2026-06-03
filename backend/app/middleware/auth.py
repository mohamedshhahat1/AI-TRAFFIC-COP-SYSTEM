"""
Authentication Middleware
Provides API key and JWT-based authentication for the Traffic Cop API.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import hmac
import hashlib

from ..config import settings


# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def api_key_auth(api_key: Optional[str] = Depends(api_key_header)) -> Optional[str]:
    """
    Validate API key if API_KEY is configured.
    If no API_KEY is set in environment, authentication is bypassed (dev mode).
    """
    if not settings.API_KEY:
        # No API key configured - allow all requests (development mode)
        return "dev-user"

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not hmac.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )

    return api_key


async def get_current_user(api_key: str = Depends(api_key_auth)) -> str:
    """Get the current authenticated user/key."""
    return api_key
