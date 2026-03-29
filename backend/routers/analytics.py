from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date, extract
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone, date
from typing import Optional

from database import get_db
from models.session import ChargingSession, SessionStatus
from models.plug import Plug
from models.user import User
from auth import get_current_user, require_admin

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class DailySummary(BaseModel):
    date: str
    total_kwh: float
    total_cost: float
    session_count: int


class OverallStats(BaseModel):
    total_sessions: int
    total_kwh: float
    total_cost: float
    active_sessions: int
    avg_kwh_per_session: float


class PlugUsage(BaseModel):
    plug_id: int
    plug_name: str
    total_sessions: int
    total_kwh: float


@router.get("/me/summary", response_model=OverallStats)
async def my_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(
            func.count(ChargingSession.id).label("total"),
            func.coalesce(func.sum(ChargingSession.energy_kwh), 0).label("kwh"),
            func.coalesce(func.sum(ChargingSession.total_coins_spent), 0).label("cost"),
        ).where(
            ChargingSession.user_id == user.id,
            ChargingSession.status != SessionStatus.active,
        )
    )
    row = result.one()

    active_result = await db.execute(
        select(func.count(ChargingSession.id)).where(
            ChargingSession.user_id == user.id,
            ChargingSession.status == SessionStatus.active,
        )
    )
    active_count = active_result.scalar_one()

    total = row.total or 0
    kwh = float(row.kwh or 0)
    return OverallStats(
        total_sessions=total,
        total_kwh=round(kwh, 3),
        total_cost=round(float(row.cost or 0), 2),
        active_sessions=active_count,
        avg_kwh_per_session=round(kwh / total, 3) if total > 0 else 0.0,
    )


@router.get("/me/daily", response_model=list[DailySummary])
async def my_daily(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            cast(ChargingSession.started_at, Date).label("day"),
            func.coalesce(func.sum(ChargingSession.energy_kwh), 0).label("kwh"),
            func.coalesce(func.sum(ChargingSession.total_coins_spent), 0).label("cost"),
            func.count(ChargingSession.id).label("cnt"),
        )
        .where(
            ChargingSession.user_id == user.id,
            ChargingSession.started_at >= since,
            ChargingSession.status != SessionStatus.active,
        )
        .group_by(cast(ChargingSession.started_at, Date))
        .order_by(cast(ChargingSession.started_at, Date))
    )
    rows = result.all()
    return [
        DailySummary(
            date=str(r.day),
            total_kwh=round(float(r.kwh), 3),
            total_cost=round(float(r.cost), 2),
            session_count=r.cnt,
        )
        for r in rows
    ]


@router.get("/admin/overview", response_model=OverallStats)
async def admin_overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(
        select(
            func.count(ChargingSession.id).label("total"),
            func.coalesce(func.sum(ChargingSession.energy_kwh), 0).label("kwh"),
            func.coalesce(func.sum(ChargingSession.total_coins_spent), 0).label("cost"),
        ).where(ChargingSession.status != SessionStatus.active)
    )
    row = result.one()
    active_result = await db.execute(
        select(func.count(ChargingSession.id)).where(
            ChargingSession.status == SessionStatus.active
        )
    )
    active = active_result.scalar_one()
    total = row.total or 0
    kwh = float(row.kwh or 0)
    return OverallStats(
        total_sessions=total,
        total_kwh=round(kwh, 3),
        total_cost=round(float(row.cost or 0), 2),
        active_sessions=active,
        avg_kwh_per_session=round(kwh / total, 3) if total > 0 else 0.0,
    )


@router.get("/admin/plug-usage", response_model=list[PlugUsage])
async def plug_usage(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(
        select(
            ChargingSession.plug_id,
            func.count(ChargingSession.id).label("sessions"),
            func.coalesce(func.sum(ChargingSession.energy_kwh), 0).label("kwh"),
        )
        .where(ChargingSession.status != SessionStatus.active)
        .group_by(ChargingSession.plug_id)
    )
    rows = result.all()
    out = []
    for r in rows:
        plug = await db.get(Plug, r.plug_id)
        out.append(PlugUsage(
            plug_id=r.plug_id,
            plug_name=plug.name if plug else f"Plug #{r.plug_id}",
            total_sessions=r.sessions,
            total_kwh=round(float(r.kwh), 3),
        ))
    return out
