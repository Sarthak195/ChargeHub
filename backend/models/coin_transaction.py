from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Float, DateTime, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
import enum


class CoinTxType(str, enum.Enum):
    topup = "topup"           # user bought coins (via Stripe or admin credit)
    session_debit = "session_debit"  # coins spent during a charging session
    admin_credit = "admin_credit"    # admin manually adds coins
    refund = "refund"         # session cancelled, coins refunded


class CoinTransaction(Base):
    __tablename__ = "coin_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("charging_sessions.id"), nullable=True)

    amount: Mapped[float] = mapped_column(Float, nullable=False)   # positive = credit, negative = debit
    tx_type: Mapped[CoinTxType] = mapped_column(SAEnum(CoinTxType), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)   # snapshot of balance after tx

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="coin_transactions")
