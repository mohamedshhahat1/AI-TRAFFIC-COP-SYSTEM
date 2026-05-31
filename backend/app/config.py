"""
Application Configuration
Environment-based settings for the backend server.
"""

import os
from dataclasses import dataclass


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
    
    # CORS
    CORS_ORIGINS: list = None
    
    # Alerts
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")
    
    def __post_init__(self):
        if self.CORS_ORIGINS is None:
            self.CORS_ORIGINS = ["*"]


settings = Settings()
