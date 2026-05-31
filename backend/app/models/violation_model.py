"""Violation database model."""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class ViolationModel(Base):
    __tablename__ = "violations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    violation_id = Column(String(50), unique=True, index=True)
    type = Column(String(50), index=True)
    severity = Column(String(20), index=True)
    track_id = Column(Integer)
    vehicle_class = Column(String(30))
    speed = Column(Float, default=0.0)
    speed_limit = Column(Float, default=60.0)
    description = Column(String(500))
    snapshot_path = Column(String(255))
    confirmed = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "violation_id": self.violation_id,
            "type": self.type,
            "severity": self.severity,
            "track_id": self.track_id,
            "vehicle_class": self.vehicle_class,
            "speed": self.speed,
            "description": self.description,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
