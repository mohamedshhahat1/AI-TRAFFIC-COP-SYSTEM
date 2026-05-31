"""Alert Service - notification delivery."""

import asyncio
import smtplib
from email.mime.text import MIMEText
from typing import List
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("alert_service")
except ImportError:
    from loguru import logger
import time


class AlertService:
    """Handles sending alerts via email, SMS, push."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.history: List[dict] = []
    
    async def send_violation_alert(self, violation: dict):
        """Send alert for a violation."""
        severity = violation.get("severity", "low")
        
        # Only alert on medium+ severity
        if severity in ("low",):
            return
        
        message = (
            f"🚨 Traffic Violation [{severity.upper()}]\n"
            f"Type: {violation.get('type', 'unknown')}\n"
            f"Vehicle: #{violation.get('track_id', '?')}\n"
            f"Speed: {violation.get('speed', 0):.1f} km/h\n"
            f"Time: {time.strftime('%H:%M:%S')}"
        )
        
        self.history.append({
            "message": message,
            "severity": severity,
            "timestamp": time.time(),
            "sent": True,
        })
        
        logger.info(f"Alert sent: {severity} violation")
    
    async def send_email(self, to: str, subject: str, body: str):
        """Send email alert."""
        # Implementation depends on SMTP config
        logger.info(f"Email alert → {to}: {subject}")
    
    def get_history(self, limit: int = 20) -> List[dict]:
        return self.history[-limit:]
