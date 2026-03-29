import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from datetime import datetime, timezone

from database import get_db
from models.payment import Payment, PaymentStatus
from models.session import ChargingSession, SessionStatus
from models.user import User
from auth import get_current_user
import services.stripe_service as stripe_svc
from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments"])
settings = get_settings()


class SetupIntentResponse(BaseModel):
    client_secret: str
    stripe_publishable_key: str


class PaymentIntentRequest(BaseModel):
    session_id: int


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount_usd: float
    stripe_publishable_key: str


@router.get("/setup-intent", response_model=SetupIntentResponse)
async def create_setup_intent(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns a Stripe SetupIntent client_secret to let the user save a card."""
    if not user.stripe_customer_id:
        cid = await stripe_svc.get_or_create_stripe_customer(user.email, user.full_name)
        user.stripe_customer_id = cid
        db.add(user)
        await db.commit()

    client_secret = await stripe_svc.create_setup_intent(user.stripe_customer_id)
    return SetupIntentResponse(
        client_secret=client_secret,
        stripe_publishable_key=settings.stripe_publishable_key,
    )


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    body: PaymentIntentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a Stripe PaymentIntent for a completed session."""
    session = await db.get(ChargingSession, body.session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(403, "Not your session")
    if session.status not in (SessionStatus.payment_pending, SessionStatus.completed):
        raise HTTPException(400, "Session is not awaiting payment")

    payment_data = await stripe_svc.create_payment_intent(session, user.stripe_customer_id)
    return PaymentIntentResponse(
        client_secret=payment_data["client_secret"],
        payment_intent_id=payment_data["payment_intent_id"],
        amount_usd=payment_data["amount_usd"],
        stripe_publishable_key=settings.stripe_publishable_key,
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Stripe sends events here — mark payment as succeeded."""
    payload = await request.body()
    try:
        event = stripe_svc.verify_webhook(payload, stripe_signature or "")
    except Exception as e:
        logger.error(f"Stripe webhook verification failed: {e}")
        raise HTTPException(400, "Invalid webhook signature")

    if event.type == "payment_intent.succeeded":
        pi = event.data.object
        session_id = int(pi.metadata.get("chargehub_session_id", 0))
        if session_id:
            # Update payment record
            await db.execute(
                update(Payment)
                .where(Payment.stripe_payment_intent_id == pi.id)
                .values(status=PaymentStatus.succeeded, paid_at=datetime.now(timezone.utc))
            )
            # Mark session as paid
            await db.execute(
                update(ChargingSession)
                .where(ChargingSession.id == session_id)
                .values(status=SessionStatus.paid)
            )
            await db.commit()
            logger.info(f"Session {session_id} marked as PAID via Stripe webhook")

    elif event.type == "payment_intent.payment_failed":
        pi = event.data.object
        await db.execute(
            update(Payment)
            .where(Payment.stripe_payment_intent_id == pi.id)
            .values(status=PaymentStatus.failed)
        )
        await db.commit()

    return {"received": True}
