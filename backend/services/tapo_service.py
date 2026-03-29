"""
Tapo service — controls P110 plugs over local LAN.

Uses python-kasa (which supports both legacy and KLAP/newer Tapo firmware).
Falls back to the `tapo` PyPI library if kasa fails.
Both work fully offline/locally — no cloud needed after initial setup.
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class PlugState:
    is_on: bool
    current_power_w: float
    today_energy_kwh: float
    signal_strength: Optional[int] = None
    nickname: Optional[str] = None


# ── python-kasa implementation (preferred — handles KLAP protocol) ─────────

async def _kasa_get_state(ip: str) -> Optional[PlugState]:
    try:
        from kasa import Discover, Credentials
        dev = await asyncio.wait_for(
            Discover.discover_single(
                ip,
                credentials=Credentials(settings.tapo_username, settings.tapo_password),
            ),
            timeout=12.0,
        )
        await asyncio.wait_for(dev.update(), timeout=10.0)

        # Energy data (P110 specific)
        power_w = 0.0
        today_kwh = 0.0
        try:
            if hasattr(dev, 'modules'):
                energy_mod = dev.modules.get("Energy") or dev.modules.get("energy")
                if energy_mod:
                    realtime = getattr(energy_mod, 'current_consumption', None)
                    if realtime is not None:
                        power_w = float(realtime)
                    today_kwh = float(getattr(energy_mod, 'consumption_today', 0) or 0)
        except Exception:
            pass

        state = PlugState(
            is_on=dev.is_on,
            current_power_w=power_w,
            today_energy_kwh=today_kwh,
            nickname=dev.alias,
        )
        await dev.disconnect()
        return state
    except Exception as e:
        logger.debug(f"kasa failed for {ip}: {type(e).__name__}: {e}")
        return None



async def _kasa_turn_on(ip: str) -> bool:
    try:
        from kasa import Discover, Credentials
        dev = await asyncio.wait_for(
            Discover.discover_single(ip, credentials=Credentials(settings.tapo_username, settings.tapo_password)),
            timeout=12.0,
        )
        await asyncio.wait_for(dev.update(), timeout=8.0)
        await asyncio.wait_for(dev.turn_on(), timeout=8.0)
        await dev.disconnect()
        return True
    except Exception as e:
        logger.debug(f"kasa turn_on failed for {ip}: {e}")
        return False


async def _kasa_turn_off(ip: str) -> bool:
    try:
        from kasa import Discover, Credentials
        dev = await asyncio.wait_for(
            Discover.discover_single(ip, credentials=Credentials(settings.tapo_username, settings.tapo_password)),
            timeout=12.0,
        )
        await asyncio.wait_for(dev.update(), timeout=8.0)
        await asyncio.wait_for(dev.turn_off(), timeout=8.0)
        await dev.disconnect()
        return True
    except Exception as e:
        logger.debug(f"kasa turn_off failed for {ip}: {e}")
        return False


# ── tapo library fallback ──────────────────────────────────────────────────

async def _tapo_get_state(ip: str) -> Optional[PlugState]:
    try:
        from tapo import ApiClient
        client = ApiClient(settings.tapo_username, settings.tapo_password)
        device = await asyncio.wait_for(client.p110(ip), timeout=10.0)
        device_info = await asyncio.wait_for(device.get_device_info(), timeout=8.0)
        current_power = await asyncio.wait_for(device.get_current_power(), timeout=8.0)
        device_usage = await asyncio.wait_for(device.get_device_usage(), timeout=8.0)

        today_wh = device_usage.to_dict().get("today_energy", 0) or 0
        power_w = float(current_power.to_dict().get("current_power", 0) or 0)

        return PlugState(
            is_on=device_info.to_dict().get("device_on", False),
            current_power_w=power_w,
            today_energy_kwh=today_wh / 1000.0,
            nickname=device_info.to_dict().get("nickname", None),
        )
    except Exception as e:
        logger.debug(f"tapo fallback failed for {ip}: {type(e).__name__}: {e}")
        return None


# ── Public API ─────────────────────────────────────────────────────────────

async def get_plug_state(ip_address: str) -> Optional[PlugState]:
    """
    Poll a P110 plug for its current state.
    Tries python-kasa first (KLAP protocol, works with newer firmware),
    then falls back to the tapo library.
    Returns None if the plug is unreachable with both methods.
    """
    if not settings.tapo_username or settings.tapo_username == "your_tplink_email@example.com":
        return _mock_plug_state(ip_address)

    # Try kasa first
    state = await _kasa_get_state(ip_address)
    if state is not None:
        return state

    # Fall back to tapo library
    state = await _tapo_get_state(ip_address)
    if state is not None:
        return state

    logger.warning(f"Plug {ip_address} unreachable via both kasa and tapo")
    return None


async def turn_on_plug(ip_address: str) -> bool:
    """Turn the plug ON."""
    if not settings.tapo_username or settings.tapo_username == "your_tplink_email@example.com":
        logger.info(f"[MOCK] Turning ON plug {ip_address}")
        _mock_states[ip_address] = {**_mock_states.get(ip_address, {"energy": 0.0}), "is_on": True, "power": 0.0}
        return True

    if await _kasa_turn_on(ip_address):
        logger.info(f"Plug {ip_address} turned ON via kasa")
        return True
    # fallback
    try:
        from tapo import ApiClient
        client = ApiClient(settings.tapo_username, settings.tapo_password)
        device = await asyncio.wait_for(client.p110(ip_address), timeout=10.0)
        await asyncio.wait_for(device.on(), timeout=8.0)
        logger.info(f"Plug {ip_address} turned ON via tapo fallback")
        return True
    except Exception as e:
        logger.error(f"Failed to turn ON plug {ip_address}: {e}")
        return False


async def turn_off_plug(ip_address: str) -> bool:
    """Turn the plug OFF."""
    if not settings.tapo_username or settings.tapo_username == "your_tplink_email@example.com":
        logger.info(f"[MOCK] Turning OFF plug {ip_address}")
        if ip_address in _mock_states:
            _mock_states[ip_address]["is_on"] = False
        return True

    if await _kasa_turn_off(ip_address):
        logger.info(f"Plug {ip_address} turned OFF via kasa")
        return True
    try:
        from tapo import ApiClient
        client = ApiClient(settings.tapo_username, settings.tapo_password)
        device = await asyncio.wait_for(client.p110(ip_address), timeout=10.0)
        await asyncio.wait_for(device.off(), timeout=8.0)
        logger.info(f"Plug {ip_address} turned OFF via tapo fallback")
        return True
    except Exception as e:
        logger.error(f"Failed to turn OFF plug {ip_address}: {e}")
        return False


async def get_hourly_energy(ip_address: str) -> list[dict]:
    """Get today's hourly energy data from the plug."""
    if not settings.tapo_username or settings.tapo_username == "your_tplink_email@example.com":
        return _mock_hourly_energy()
    try:
        from datetime import datetime, timezone
        from tapo.requests import EnergyDataInterval
        from tapo import ApiClient
        client = ApiClient(settings.tapo_username, settings.tapo_password)
        device = await asyncio.wait_for(client.p110(ip_address), timeout=10.0)
        today = datetime.now(timezone.utc)
        data = await asyncio.wait_for(
            device.get_energy_data(EnergyDataInterval.Hourly, today), timeout=10.0
        )
        entries = data.to_dict().get("data", [])
        return [{"hour": i, "energy_wh": v} for i, v in enumerate(entries)]
    except Exception as e:
        logger.error(f"Error fetching hourly energy for {ip_address}: {e}")
        return []


# ── Mock helpers ───────────────────────────────────────────────────────────

import random

_mock_states: dict[str, dict] = {}


def _mock_plug_state(ip: str) -> PlugState:
    state = _mock_states.get(ip, {"is_on": False, "power": 0.0, "energy": 0.0})
    if state["is_on"]:
        state["power"] = round(random.uniform(1000, 2400), 1)
        state["energy"] = round(state.get("energy", 0) + state["power"] / 3600 / 1000, 4)
    else:
        state["power"] = 0.0
    _mock_states[ip] = state
    return PlugState(
        is_on=state["is_on"],
        current_power_w=state["power"],
        today_energy_kwh=state["energy"],
        nickname=f"Mock Plug {ip}",
    )


def _mock_hourly_energy() -> list[dict]:
    return [{"hour": h, "energy_wh": random.randint(0, 500) if h < 8 else 0} for h in range(24)]
