"""
Application Configuration
Environment-based settings for the backend server.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Settings:
    """Application settings."""
    APP_NAME: str = "AI Traffic Cop System API"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./data/traffic_cop.db"
    )

    # CORS - defaults to localhost dev origins; override with comma-separated CORS_ORIGINS env var
    CORS_ORIGINS: List[str] = field(default=None)

    # Authentication
    API_KEY: str = os.getenv("API_KEY", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")

    # Alerts
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "600"))

    def __post_init__(self):
        if self.CORS_ORIGINS is None:
            origins_env = os.getenv("CORS_ORIGINS", "")
            if origins_env:
                self.CORS_ORIGINS = [o.strip() for o in origins_env.split(",")]
            else:
                self.CORS_ORIGINS = [
                    "http://localhost:3000",
                    "http://localhost:8000",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:8000",
                ]


settings = Settings()
