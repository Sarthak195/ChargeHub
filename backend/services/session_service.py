"""
Session service — business logic for charging session lifecycle (coin-based billing).
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models.session import ChargingSession, SessionStatus
from models.plug import Plug, PlugStatus
from models.user import User
from models.coin_transaction import CoinTransaction, CoinTxType
from config import get_settings
import services.tapo_service as tapo

logger = logging.getLogger(__name__)
settings = get_settings()


async def _charge_coins(
    db: AsyncSession,
    user: User,
    amount: float,
    tx_type: CoinTxType,
    description: str,
    session_id: int | None = None,
) -> None:
    """Deduct (negative amount) or credit (positive amount) coins from a user's balance."""
    user.coin_balance = round(user.coin_balance + amount, 4)
    db.add(user)
    tx = CoinTransaction(
        user_id=user.id,
        session_id=session_id,
        amount=amount,
        tx_type=tx_type,
        description=description,
        balance_after=user.coin_balance,
    )
    db.add(tx)


async def start_session(db: AsyncSession, user_id: int, plug_id: int) -> ChargingSession:
    """
    Start a new charging session:
    1. Verify plug is available
    2. Check user has enough coins (must have > 0)
    3. Turn plug ON
    4. Create session record with locked-in rates
    """
    user = await db.get(User, user_id)
    plug = await db.get(Plug, plug_id)

    if not plug:
        raise ValueError("Plug not found")
    if plug.status != PlugStatus.available:
        raise ValueError(f"Plug is not available (status: {plug.status.value})")
    if user.coin_balance <= 0:
        raise ValueError("Insufficient coin balance. Please top up before charging.")

    success = await tapo.turn_on_plug(plug.ip_address)
    if not success:
        raise RuntimeError("Failed to communicate with the plug. It may be offline.")

    session = ChargingSession(
        user_id=user_id,
        plug_id=plug_id,
        coins_per_kwh=settings.coins_per_kwh,
        coins_per_minute=settings.coins_per_minute,
        energy_snapshots=[],
    )
    db.add(session)
    plug.status = PlugStatus.occupied
    db.add(plug)

    await db.commit()
    await db.refresh(session)
    return session


async def stop_session(db: AsyncSession, session_id: int, user_id: int) -> ChargingSession:
    """
    Stop a charging session and settle the coin bill:
    - Total coins = (kWh × coins_per_kwh) + (minutes × coins_per_minute)
    - Deduct from user's coin balance (cap deduction at actual balance)
    """
    session = await db.get(ChargingSession, session_id)
    if not session:
        raise ValueError("Session not found")
    if session.user_id != user_id:
        raise PermissionError("Not your session")
    if session.status != SessionStatus.active:
        raise ValueError("Session is not active")

    plug = await db.get(Plug, session.plug_id)
    user = await db.get(User, user_id)

    # Turn off plug
    if plug:
        await tapo.turn_off_plug(plug.ip_address)
        plug.status = PlugStatus.available
        plug.current_power_w = 0.0
        db.add(plug)

    # Calculate coin cost
    ended_at = datetime.now(timezone.utc)
    duration_minutes = (ended_at - session.started_at).total_seconds() / 60
    coins_for_energy = session.energy_kwh * session.coins_per_kwh
    coins_for_time = duration_minutes * session.coins_per_minute
    total_coins = round(coins_for_energy + coins_for_time, 2)
    # Deduct at most what the user has
    deduction = min(total_coins, user.coin_balance)

    session.ended_at = ended_at
    session.total_coins_spent = total_coins
    session.status = SessionStatus.paid
    db.add(session)

    await _charge_coins(
        db, user,
        amount=-deduction,
        tx_type=CoinTxType.session_debit,
        description=f"Session #{session.id}: {round(session.energy_kwh, 3)} kWh, {round(duration_minutes, 1)} min",
        session_id=session.id,
    )

    await db.commit()
    await db.refresh(session)
    return session


async def record_energy_snapshot(
    db: AsyncSession,
    session: ChargingSession,
    power_w: float,
    elapsed_seconds: float,
) -> None:
    """Called by background scheduler — accumulates kWh and trickle-deducts coins."""
    kwh_increment = (power_w * elapsed_seconds / 3600) / 1000
    session.energy_kwh = round(session.energy_kwh + kwh_increment, 6)
    if power_w > session.peak_power_w:
        session.peak_power_w = power_w

    snapshot = {
        "ts": int(datetime.now(timezone.utc).timestamp()),
        "watts": power_w,
        "kwh_total": session.energy_kwh,
    }
    session.energy_snapshots = [*session.energy_snapshots, snapshot]

    await db.execute(
        update(ChargingSession)
        .where(ChargingSession.id == session.id)
        .values(
            energy_kwh=session.energy_kwh,
            peak_power_w=session.peak_power_w,
            energy_snapshots=session.energy_snapshots,
        )
    )
    await db.commit()


async def get_active_session_for_user(db: AsyncSession, user_id: int) -> Optional[ChargingSession]:
    result = await db.execute(
        select(ChargingSession).where(
            ChargingSession.user_id == user_id,
            ChargingSession.status == SessionStatus.active,
        )
    )
    return result.scalar_one_or_none()
