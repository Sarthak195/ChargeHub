from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.plug import Plug, PlugStatus
from auth import get_current_user, require_admin
from models.user import User
import services.tapo_service as tapo

router = APIRouter(prefix="/api/plugs", tags=["plugs"])


class PlugResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    location_description: Optional[str]
    slot_number: Optional[int]
    status: str
    current_power_w: float

    model_config = {"from_attributes": True}


class CreatePlugRequest(BaseModel):
    name: str
    ip_address: str
    location_description: Optional[str] = None
    slot_number: Optional[int] = None


class UpdatePlugRequest(BaseModel):
    name: Optional[str] = None
    location_description: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/", response_model=list[PlugResponse])
async def list_plugs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all active plugs with live status — used for the parking map."""
    result = await db.execute(select(Plug).where(Plug.is_active == True).order_by(Plug.slot_number))
    plugs = result.scalars().all()
    return [PlugResponse.model_validate(p) for p in plugs]


@router.get("/{plug_id}", response_model=PlugResponse)
async def get_plug(
    plug_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    plug = await db.get(Plug, plug_id)
    if not plug:
        raise HTTPException(404, "Plug not found")
    return PlugResponse.model_validate(plug)


@router.post("/", response_model=PlugResponse, status_code=201)
async def create_plug(
    body: CreatePlugRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — register a new P110 plug."""
    plug = Plug(
        name=body.name,
        ip_address=body.ip_address,
        location_description=body.location_description,
        slot_number=body.slot_number,
    )
    db.add(plug)
    await db.commit()
    await db.refresh(plug)
    return PlugResponse.model_validate(plug)


@router.patch("/{plug_id}", response_model=PlugResponse)
async def update_plug(
    plug_id: int,
    body: UpdatePlugRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    plug = await db.get(Plug, plug_id)
    if not plug:
        raise HTTPException(404, "Plug not found")
    if body.name is not None:
        plug.name = body.name
    if body.location_description is not None:
        plug.location_description = body.location_description
    if body.status is not None:
        plug.status = PlugStatus(body.status)
    if body.is_active is not None:
        plug.is_active = body.is_active
    db.add(plug)
    await db.commit()
    await db.refresh(plug)
    return PlugResponse.model_validate(plug)


@router.delete("/{plug_id}", status_code=204)
async def delete_plug(
    plug_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    plug = await db.get(Plug, plug_id)
    if not plug:
        raise HTTPException(404, "Plug not found")
    plug.is_active = False
    db.add(plug)
    await db.commit()


@router.post("/{plug_id}/test", response_model=dict)
async def test_plug_connection(
    plug_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin — test live connection to a plug."""
    plug = await db.get(Plug, plug_id)
    if not plug:
        raise HTTPException(404, "Plug not found")
    state = await tapo.get_plug_state(plug.ip_address)
    if state is None:
        return {"reachable": False, "ip": plug.ip_address}
    return {
        "reachable": True,
        "is_on": state.is_on,
        "current_power_w": state.current_power_w,
        "today_energy_kwh": state.today_energy_kwh,
        "nickname": state.nickname,
    }
