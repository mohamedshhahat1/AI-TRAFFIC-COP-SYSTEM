"""Vehicle database model."""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class VehicleBase(DeclarativeBase):
    pass


class VehicleModel(VehicleBase):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, unique=True, index=True)
    vehicle_class = Column(String(30))
    max_speed = Column(Float, default=0.0)
    avg_speed = Column(Float, default=0.0)
    current_speed = Column(Float, default=0.0)
    violation_count = Column(Integer, default=0)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "track_id": self.track_id,
            "vehicle_class": self.vehicle_class,
            "max_speed": self.max_speed,
            "avg_speed": self.avg_speed,
            "current_speed": self.current_speed,
            "violation_count": self.violation_count,
            "is_active": self.is_active,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }
