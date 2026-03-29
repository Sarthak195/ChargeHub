from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, Float, Enum as SAEnum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
import enum


class SessionStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    paid = "paid"          # coins already deducted — "paid" means settled
    cancelled = "cancelled"


class ChargingSession(Base):
    __tablename__ = "charging_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    plug_id: Mapped[int] = mapped_column(ForeignKey("plugs.id"), nullable=False, index=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Energy tracking
    energy_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    peak_power_w: Mapped[float] = mapped_column(Float, default=0.0)
    energy_snapshots: Mapped[list] = mapped_column(JSON, default=list)  # [{ts, watts, kwh_total}]

    # Coin billing — locked-in rates at session start
    coins_per_kwh: Mapped[float] = mapped_column(Float, default=10.0)
    coins_per_minute: Mapped[float] = mapped_column(Float, default=0.5)
    total_coins_spent: Mapped[float] = mapped_column(Float, default=0.0)

    status: Mapped[SessionStatus] = mapped_column(SAEnum(SessionStatus), default=SessionStatus.active)

    user: Mapped["User"] = relationship(back_populates="sessions")
    plug: Mapped["Plug"] = relationship(back_populates="sessions")
    payment: Mapped["Payment"] = relationship(back_populates="session", uselist=False)
