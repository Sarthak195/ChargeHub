import asyncio
import json
import logging
from typing import Optional, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel

from database import get_db
from models.session import ChargingSession, SessionStatus
from models.plug import Plug
from models.user import User
from auth import get_current_user, require_admin
import services.session_service as session_svc
import services.tapo_service as tapo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionResponse(BaseModel):
    id: int
    user_id: int
    plug_id: int
    plug_name: Optional[str] = None
    started_at: str
    ended_at: Optional[str] = None
    energy_kwh: float
    peak_power_w: float
    total_coins_spent: float
    status: str
    coins_per_kwh: float
    coins_per_minute: float

    model_config = {"from_attributes": True}


class StartSessionRequest(BaseModel):
    plug_id: int


class StopSessionResponse(BaseModel):
    session: SessionResponse
    client_secret: Optional[str] = None  # Stripe PaymentIntent client secret


def _serialize_session(s: ChargingSession, plug_name: str = None) -> SessionResponse:
    return SessionResponse(
        id=s.id,
        user_id=s.user_id,
        plug_id=s.plug_id,
        plug_name=plug_name,
        started_at=s.started_at.isoformat(),
        ended_at=s.ended_at.isoformat() if s.ended_at else None,
        energy_kwh=s.energy_kwh,
        peak_power_w=s.peak_power_w,
        total_coins_spent=s.total_coins_spent,
        status=s.status.value,
        coins_per_kwh=s.coins_per_kwh,
        coins_per_minute=s.coins_per_minute,
    )


@router.post("/start", response_model=SessionResponse, status_code=201)
async def start_session(
    body: StartSessionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Check if user already has an active session
    existing = await session_svc.get_active_session_for_user(db, user.id)
    if existing:
        raise HTTPException(400, "You already have an active charging session")

    try:
        session = await session_svc.start_session(db, user.id, body.plug_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))

    plug = await db.get(Plug, session.plug_id)
    return _serialize_session(session, plug_name=plug.name if plug else None)


@router.post("/{session_id}/stop", response_model=StopSessionResponse)
async def stop_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        session = await session_svc.stop_session(db, session_id, user.id)
    except (ValueError, PermissionError) as e:
        raise HTTPException(400, str(e))

    plug = await db.get(Plug, session.plug_id)

    # Create Stripe PaymentIntent if Stripe is configured
    client_secret = None
    if session.total_coins_spent > 0:
        try:
            pass  # Stripe integration optional
        except Exception as e:
            logger.error(f"Stripe error: {e}")

    return StopSessionResponse(
        session=_serialize_session(session, plug_name=plug.name if plug else None),
        client_secret=client_secret,
    )


@router.get("/active", response_model=Optional[SessionResponse])
async def get_active_session(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await session_svc.get_active_session_for_user(db, user.id)
    if not session:
        return None
    plug = await db.get(Plug, session.plug_id)
    return _serialize_session(session, plug_name=plug.name if plug else None)


@router.get("/live/{session_id}")
async def live_session_stream(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Server-Sent Events (SSE) stream for live session updates.
    Frontend listens to this for real-time wattage and kWh updates.
    """
    session = await db.get(ChargingSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(403, "Not your session")

    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            # Re-fetch session from DB
            from sqlalchemy import select as sa_select
            result = await db.execute(
                sa_select(ChargingSession).where(ChargingSession.id == session_id)
            )
            s = result.scalar_one_or_none()
            if not s or s.status != SessionStatus.active:
                yield f"data: {json.dumps({'status': 'ended'})}\n\n"
                break

            plug = await db.get(Plug, s.plug_id)
            data = {
                "session_id": s.id,
                "energy_kwh": round(s.energy_kwh, 4),
                "current_power_w": plug.current_power_w if plug else 0,
                "estimated_cost": round(s.energy_kwh * s.coins_per_kwh, 2),
                "status": s.status.value,
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history", response_model=list[SessionResponse])
async def session_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChargingSession)
        .where(ChargingSession.user_id == user.id)
        .order_by(desc(ChargingSession.started_at))
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()
    out = []
    for s in sessions:
        plug = await db.get(Plug, s.plug_id)
        out.append(_serialize_session(s, plug_name=plug.name if plug else None))
    return out


@router.get("/all", response_model=list[SessionResponse])
async def all_sessions_admin(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — all sessions across all users."""
    result = await db.execute(
        select(ChargingSession)
        .order_by(desc(ChargingSession.started_at))
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()
    out = []
    for s in sessions:
        plug = await db.get(Plug, s.plug_id)
        out.append(_serialize_session(s, plug_name=plug.name if plug else None))
    return out
