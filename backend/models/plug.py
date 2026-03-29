from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Float, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
import enum


class PlugStatus(str, enum.Enum):
    available = "available"
    occupied = "occupied"
    offline = "offline"
    maintenance = "maintenance"


class Plug(Base):
    __tablename__ = "plugs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)          # e.g. "Slot A1"
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    location_description: Mapped[str] = mapped_column(String(255), nullable=True)  # e.g. "Level 1, Row A"
    slot_number: Mapped[int] = mapped_column(Integer, nullable=True)         # parking slot number
    status: Mapped[PlugStatus] = mapped_column(SAEnum(PlugStatus), default=PlugStatus.available)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    current_power_w: Mapped[float] = mapped_column(Float, default=0.0)      # live watts from last poll
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    sessions: Mapped[list["ChargingSession"]] = relationship(back_populates="plug")
