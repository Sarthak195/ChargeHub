import asyncio, sys
sys.path.insert(0, '/app')

async def reset():
    from database import AsyncSessionLocal
    from models.plug import Plug, PlugStatus
    from models.session import ChargingSession, SessionStatus
    from sqlalchemy import select
    import logging
    logging.disable(logging.CRITICAL)

    async with AsyncSessionLocal() as db:
        # Show all plugs before
        plugs = (await db.execute(select(Plug))).scalars().all()
        for p in plugs:
            print(f'Before - Plug {p.id} ({p.name}): {p.status}')
            p.status = PlugStatus.available
            p.current_power_w = 0.0
            db.add(p)

        # Cancel all active sessions
        sessions = (await db.execute(select(ChargingSession))).scalars().all()
        for s in sessions:
            print(f'Before - Session {s.id}: plug={s.plug_id} status={s.status}')
            if s.status == SessionStatus.active:
                s.status = SessionStatus.cancelled
                db.add(s)

        await db.commit()

        # Verify
        plugs2 = (await db.execute(select(Plug))).scalars().all()
        for p in plugs2:
            print(f'After  - Plug {p.id} ({p.name}): {p.status}')

        print('RESET COMPLETE')

asyncio.run(reset())
