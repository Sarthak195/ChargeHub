"""
Seed script — creates the first admin user and registers your first P110 plug.

Usage (run inside the backend container or locally with DB running):
  python seed.py

Or via docker:
  docker exec -it chargehub_api python seed.py
"""
import asyncio
from database import AsyncSessionLocal, init_db
from models.user import User, UserRole
from models.plug import Plug
from auth import hash_password


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        # Create admin user
        from sqlalchemy import select
        existing = await db.execute(select(User).where(User.email == "admin@chargehub.local"))
        if not existing.scalar_one_or_none():
            admin = User(
                email="admin@chargehub.local",
                hashed_password=hash_password("admin123"),
                full_name="ChargeHub Admin",
                unit_number=None,
                role=UserRole.admin,
                coin_balance=9999.0,  # Admin has infinite coins for testing
            )
            db.add(admin)
            print("✓ Created admin user: admin@chargehub.local / admin123")
        else:
            print("  Admin user already exists")

        # Register first P110 plug
        existing_plug = await db.execute(select(Plug).where(Plug.ip_address == "192.168.1.51"))
        if not existing_plug.scalar_one_or_none():
            plug = Plug(
                name="Slot A1",
                ip_address="192.168.1.51",
                location_description="Level 1, Row A",
                slot_number=1,
            )
            db.add(plug)
            print("✓ Registered plug: 192.168.1.51 as 'Slot A1'")
        else:
            print("  Plug 192.168.1.51 already registered")

        await db.commit()
        print("\nSeed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
