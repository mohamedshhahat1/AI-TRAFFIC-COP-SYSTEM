"""
Alert Manager Module
Handles sending notifications through multiple channels.
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from loguru import logger
from dataclasses import dataclass
from enum import Enum
import time
import json


class AlertChannel(Enum):
    """Available alert channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


@dataclass
class AlertMessage:
    """Alert message structure."""
    title: str
    body: str
    severity: str
    violation_id: str
    channel: AlertChannel
    recipient: str
    timestamp: float = 0.0
    is_sent: bool = False
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class AlertManager:
    """
    Manages alert delivery across multiple channels.
    
    Supports:
    - Email (SMTP)
    - SMS (Twilio)
    - Push notifications (Firebase)
    - Webhooks (custom endpoints)
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize alert manager.
        
        Args:
            config: Alert configuration (channels, credentials, recipients)
        """
        self.config = config or {}
        self.alert_history: List[AlertMessage] = []
        self.is_enabled = True
        
        # Rate limiting
        self.rate_limit: Dict[str, float] = {}
        self.min_interval = 30.0  # Minimum seconds between alerts for same violation type
        
        logger.info("AlertManager initialized")
    
    async def send_alert(
        self,
        violation: dict,
        channels: List[AlertChannel] = None
    ) -> List[AlertMessage]:
        """
        Send alert for a violation through specified channels.
        
        Args:
            violation: Violation data dictionary
            channels: List of channels to send through (None = all enabled)
            
        Returns:
            List of AlertMessage objects with send status
        """
        if not self.is_enabled:
            return []
        
        # Check rate limit
        if self._is_rate_limited(violation.get("violation_type", "")):
            logger.debug("Alert rate limited, skipping")
            return []
        
        # Default to all enabled channels
        if channels is None:
            channels = self._get_enabled_channels()
        
        messages = []
        
        for channel in channels:
            message = self._create_message(violation, channel)
            
            try:
                if channel == AlertChannel.EMAIL:
                    await self._send_email(message)
                elif channel == AlertChannel.SMS:
                    await self._send_sms(message)
                elif channel == AlertChannel.PUSH:
                    await self._send_push(message)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook(message)
                
                message.is_sent = True
                logger.info(f"✅ Alert sent via {channel.value}: {message.title}")
                
            except Exception as e:
                message.error = str(e)
                logger.error(f"❌ Alert failed via {channel.value}: {e}")
            
            messages.append(message)
            self.alert_history.append(message)
        
        # Update rate limit
        self._update_rate_limit(violation.get("violation_type", ""))
        
        return messages
    
    def _create_message(self, violation: dict, channel: AlertChannel) -> AlertMessage:
        """Create an alert message from violation data."""
        severity = violation.get("severity", "unknown").upper()
        v_type = violation.get("violation_type", "unknown").replace("_", " ").title()
        track_id = violation.get("track_id", "?")
        speed = violation.get("speed", 0)
        
        title = f"🚨 [{severity}] Traffic Violation Detected"
        
        body = (
            f"Violation Type: {v_type}\n"
            f"Vehicle ID: {track_id}\n"
            f"Vehicle Class: {violation.get('vehicle_class', 'unknown')}\n"
            f"Speed: {speed:.1f} km/h\n"
            f"Severity: {severity}\n"
            f"Description: {violation.get('description', 'N/A')}\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        
        # Get recipient based on channel
        recipient = self._get_recipient(channel)
        
        return AlertMessage(
            title=title,
            body=body,
            severity=severity,
            violation_id=violation.get("violation_id", ""),
            channel=channel,
            recipient=recipient,
        )
    
    async def _send_email(self, message: AlertMessage):
        """Send alert via email (SMTP)."""
        email_config = self.config.get("email", {})
        
        if not email_config.get("enabled", False):
            raise ValueError("Email alerts not configured")
        
        smtp_host = email_config.get("smtp_host", "smtp.gmail.com")
        smtp_port = email_config.get("smtp_port", 587)
        sender = email_config.get("sender", "")
        password = email_config.get("password", "")
        
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = message.recipient
        msg["Subject"] = message.title
        msg.attach(MIMEText(message.body, "plain"))
        
        # Send in thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._smtp_send, smtp_host, smtp_port, sender, password, msg)
    
    def _smtp_send(self, host, port, sender, password, msg):
        """Synchronous SMTP send."""
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
    
    async def _send_sms(self, message: AlertMessage):
        """Send alert via SMS (Twilio)."""
        sms_config = self.config.get("sms", {})
        
        if not sms_config.get("enabled", False):
            raise ValueError("SMS alerts not configured")
        
        # Twilio integration
        try:
            from twilio.rest import Client
            
            account_sid = sms_config.get("account_sid", "")
            auth_token = sms_config.get("auth_token", "")
            from_number = sms_config.get("from_number", "")
            
            client = Client(account_sid, auth_token)
            
            client.messages.create(
                body=f"{message.title}\n{message.body}",
                from_=from_number,
                to=message.recipient
            )
        except ImportError:
            raise ValueError("Twilio package not installed")
    
    async def _send_push(self, message: AlertMessage):
        """Send push notification (Firebase)."""
        push_config = self.config.get("push", {})
        
        if not push_config.get("enabled", False):
            raise ValueError("Push notifications not configured")
        
        try:
            import firebase_admin
            from firebase_admin import messaging
            
            notification = messaging.Message(
                notification=messaging.Notification(
                    title=message.title,
                    body=message.body[:200],
                ),
                topic="traffic_violations",
            )
            
            messaging.send(notification)
        except ImportError:
            raise ValueError("Firebase package not installed")
    
    async def _send_webhook(self, message: AlertMessage):
        """Send alert to webhook URL."""
        webhook_config = self.config.get("webhook", {})
        webhook_url = webhook_config.get("url", "")
        
        if not webhook_url:
            raise ValueError("Webhook URL not configured")
        
        import aiohttp
        
        payload = {
            "title": message.title,
            "body": message.body,
            "severity": message.severity,
            "violation_id": message.violation_id,
            "timestamp": message.timestamp,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as resp:
                if resp.status != 200:
                    raise ValueError(f"Webhook returned status {resp.status}")
    
    def _get_enabled_channels(self) -> List[AlertChannel]:
        """Get list of enabled alert channels."""
        channels = []
        if self.config.get("email", {}).get("enabled"):
            channels.append(AlertChannel.EMAIL)
        if self.config.get("sms", {}).get("enabled"):
            channels.append(AlertChannel.SMS)
        if self.config.get("push", {}).get("enabled"):
            channels.append(AlertChannel.PUSH)
        if self.config.get("webhook", {}).get("url"):
            channels.append(AlertChannel.WEBHOOK)
        return channels
    
    def _get_recipient(self, channel: AlertChannel) -> str:
        """Get recipient for a channel."""
        if channel == AlertChannel.EMAIL:
            recipients = self.config.get("email", {}).get("recipients", [])
            return recipients[0] if recipients else ""
        elif channel == AlertChannel.SMS:
            numbers = self.config.get("sms", {}).get("to_numbers", [])
            return numbers[0] if numbers else ""
        elif channel == AlertChannel.PUSH:
            return "all_subscribers"
        elif channel == AlertChannel.WEBHOOK:
            return self.config.get("webhook", {}).get("url", "")
        return ""
    
    def _is_rate_limited(self, violation_type: str) -> bool:
        """Check if alerts for this type are rate limited."""
        last_sent = self.rate_limit.get(violation_type, 0)
        return (time.time() - last_sent) < self.min_interval
    
    def _update_rate_limit(self, violation_type: str):
        """Update rate limit timestamp."""
        self.rate_limit[violation_type] = time.time()
    
    def get_alert_history(self, limit: int = 50) -> List[dict]:
        """Get alert history."""
        return [
            {
                "title": a.title,
                "channel": a.channel.value,
                "recipient": a.recipient,
                "severity": a.severity,
                "is_sent": a.is_sent,
                "error": a.error,
                "timestamp": a.timestamp,
            }
            for a in self.alert_history[-limit:]
        ]
    
    def get_statistics(self) -> dict:
        """Get alert system statistics."""
        total = len(self.alert_history)
        sent = sum(1 for a in self.alert_history if a.is_sent)
        failed = sum(1 for a in self.alert_history if not a.is_sent)
        
        return {
            "total_alerts": total,
            "sent_successfully": sent,
            "failed": failed,
            "success_rate": sent / total if total > 0 else 0,
            "enabled_channels": [c.value for c in self._get_enabled_channels()],
        }
    
    def enable(self):
        """Enable the alert system."""
        self.is_enabled = True
        logger.info("Alert system enabled")
    
    def disable(self):
        """Disable the alert system."""
        self.is_enabled = False
        logger.info("Alert system disabled")
