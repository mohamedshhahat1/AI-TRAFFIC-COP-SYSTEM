"""Alert Service - notification delivery via email."""

import asyncio
from typing import List
try:
    from ai_engine.monitoring.logger import SystemLogger
    logger = SystemLogger("alert_service")
except ImportError:
    from loguru import logger
import time

from ..config import settings


class AlertService:
    """Handles sending alerts via email."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.history: List[dict] = []
        self._max_history = 200

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

        sent = False
        if settings.ALERT_EMAIL and settings.SMTP_HOST:
            try:
                await self.send_email(
                    to=settings.ALERT_EMAIL,
                    subject=f"[Traffic Cop] {severity.upper()} Violation Alert",
                    body=message,
                )
                sent = True
            except Exception as e:
                logger.error(f"Failed to send alert email: {e}")

        self.history.append({
            "message": message,
            "severity": severity,
            "timestamp": time.time(),
            "sent": sent,
        })

        # Trim history
        if len(self.history) > self._max_history:
            self.history = self.history[-self._max_history:]

        logger.info(f"Alert {'sent' if sent else 'logged'}: {severity} violation")

    async def send_email(self, to: str, subject: str, body: str):
        """Send email alert using SMTP."""
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = settings.ALERT_EMAIL or "noreply@traffic-cop.local"
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                start_tls=True,
            )
            logger.info(f"Email sent to {to}: {subject}")
        except ImportError:
            logger.warning("aiosmtplib not installed - email alerts disabled")
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise

    def get_history(self, limit: int = 20) -> List[dict]:
        return self.history[-limit:]
