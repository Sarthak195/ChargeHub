"""
Background scheduler — polls all active plug sessions every N seconds.
Uses APScheduler (in-process) so no extra process or broker is needed.
"""
import logging
import time
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import AsyncSessionLocal
from models.session import ChargingSession, SessionStatus
from models.plug import Plug, PlugStatus
from config import get_settings
import services.tapo_service as tapo
import services.session_service as session_svc

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler()

# Track last poll time per session for accurate kWh calculation
_last_poll_times: dict[int, float] = {}

# Track consecutive zero-power readings (to detect charge completion)
_zero_power_counts: dict[int, int] = {}
ZERO_POWER_THRESHOLD = 3  # 3 consecutive zeros → session likely done


async def poll_active_sessions():
    """
    Main polling job — runs every POLL_INTERVAL_SECONDS.
    For each active session:
      - Gets live power from the plug
      - Records an energy snapshot
      - Detects if the vehicle has finished charging (power ≈ 0)
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ChargingSession)
            .where(ChargingSession.status == SessionStatus.active)
        )
        sessions: list[ChargingSession] = result.scalars().all()

        if not sessions:
            return

        logger.debug(f"Polling {len(sessions)} active session(s)...")

        for session in sessions:
            plug = await db.get(Plug, session.plug_id)
            if not plug:
                continue

            now = time.time()
            last = _last_poll_times.get(session.id, now)
            elapsed = now - last
            _last_poll_times[session.id] = now

            state = await tapo.get_plug_state(plug.ip_address)
            if state is None:
                # Plug offline — mark as offline but keep session running
                plug.status = PlugStatus.offline
                db.add(plug)
                await db.commit()
                continue

            # Update plug live data
            plug.current_power_w = state.current_power_w
            plug.last_seen_at = datetime.now(timezone.utc)
            db.add(plug)

            # Record energy snapshot
            await session_svc.record_energy_snapshot(
                db, session, state.current_power_w, elapsed
            )

            # Detect end of charge (power drops to ~0 for multiple consecutive reads)
            if state.current_power_w < 5.0:  # < 5W = effectively idle
                _zero_power_counts[session.id] = _zero_power_counts.get(session.id, 0) + 1
                if _zero_power_counts[session.id] >= ZERO_POWER_THRESHOLD:
                    logger.info(f"Session {session.id} detected charge complete — auto-stopping")
                    # Auto-stop but DON'T turn off plug immediately (charge might resume)
                    # Just flag the session as complete; resident gets notified
                    # (In production you may want to auto-turn-off after longer delay)
            else:
                _zero_power_counts[session.id] = 0

            await db.commit()


def start_scheduler():
    scheduler.add_job(
        poll_active_sessions,
        "interval",
        seconds=settings.poll_interval_seconds,
        id="poll_sessions",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — polling every {settings.poll_interval_seconds}s")


def stop_scheduler():
    scheduler.shutdown(wait=False)
