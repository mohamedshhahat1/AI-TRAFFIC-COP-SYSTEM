"""
Database Models
SQLAlchemy models for violations, vehicles, and alerts.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Violation(Base):
    """Violation database model."""
    __tablename__ = "violations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    violation_id = Column(String(50), unique=True, nullable=False, index=True)
    violation_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    
    # Vehicle info
    track_id = Column(Integer, nullable=False)
    vehicle_class = Column(String(30), default="unknown")
    
    # Location & time
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    location_x = Column(Integer, default=0)
    location_y = Column(Integer, default=0)
    
    # Details
    speed = Column(Float, default=0.0)
    speed_limit = Column(Float, default=60.0)
    confidence = Column(Float, default=0.0)
    description = Column(Text, default="")
    
    # Evidence
    frame_snapshot = Column(String(255), nullable=True)
    
    # Status
    is_confirmed = Column(Boolean, default=False)
    is_reported = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "violation_id": self.violation_id,
            "violation_type": self.violation_type,
            "severity": self.severity,
            "track_id": self.track_id,
            "vehicle_class": self.vehicle_class,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "location": {"x": self.location_x, "y": self.location_y},
            "speed": self.speed,
            "speed_limit": self.speed_limit,
            "confidence": self.confidence,
            "description": self.description,
            "frame_snapshot": self.frame_snapshot,
            "is_confirmed": self.is_confirmed,
            "is_reported": self.is_reported,
        }


class Vehicle(Base):
    """Tracked vehicle database model."""
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, unique=True, nullable=False, index=True)
    vehicle_class = Column(String(30), default="unknown")
    
    # Tracking info
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    total_frames = Column(Integer, default=0)
    
    # Speed info
    max_speed = Column(Float, default=0.0)
    avg_speed = Column(Float, default=0.0)
    
    # Violation count
    violation_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "track_id": self.track_id,
            "vehicle_class": self.vehicle_class,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "total_frames": self.total_frames,
            "max_speed": self.max_speed,
            "avg_speed": self.avg_speed,
            "violation_count": self.violation_count,
            "is_active": self.is_active,
        }


class Alert(Base):
    """Alert notification model."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    violation_id = Column(String(50), nullable=False)
    alert_type = Column(String(20), nullable=False)  # email, sms, push
    
    recipient = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_sent = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "violation_id": self.violation_id,
            "alert_type": self.alert_type,
            "recipient": self.recipient,
            "message": self.message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "is_sent": self.is_sent,
        }
