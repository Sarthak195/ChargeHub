"""
Stripe service — handles payment intents and webhook handling.
"""
import logging
import stripe
from config import get_settings
from models.session import ChargingSession, SessionStatus
from models.payment import Payment, PaymentStatus

logger = logging.getLogger(__name__)
settings = get_settings()

stripe.api_key = settings.stripe_secret_key


async def create_payment_intent(session: ChargingSession, stripe_customer_id: str | None) -> dict:
    """
    Create a Stripe PaymentIntent for a completed charging session.
    Returns client_secret to the frontend to confirm the payment.
    """
    amount_cents = int(session.total_cost * 100)  # Stripe uses smallest currency unit
    if amount_cents < 50:
        amount_cents = 50  # Stripe minimum

    intent_params = {
        "amount": amount_cents,
        "currency": "usd",
        "metadata": {
            "chargehub_session_id": str(session.id),
            "user_id": str(session.user_id),
            "energy_kwh": str(round(session.energy_kwh, 3)),
        },
    }
    if stripe_customer_id:
        intent_params["customer"] = stripe_customer_id

    try:
        intent = stripe.PaymentIntent.create(**intent_params)
        return {
            "payment_intent_id": intent.id,
            "client_secret": intent.client_secret,
            "amount_usd": session.total_cost,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating payment intent: {e}")
        raise RuntimeError(f"Payment processing error: {str(e)}")


async def create_setup_intent(stripe_customer_id: str) -> str:
    """Create a SetupIntent for saving a card without immediate charge."""
    intent = stripe.SetupIntent.create(customer=stripe_customer_id)
    return intent.client_secret


async def get_or_create_stripe_customer(email: str, name: str) -> str:
    """Get or create a Stripe Customer record. Returns customer ID."""
    customers = stripe.Customer.list(email=email, limit=1)
    if customers.data:
        return customers.data[0].id
    customer = stripe.Customer.create(email=email, name=name)
    return customer.id


def verify_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify and parse a Stripe webhook event."""
    return stripe.Webhook.construct_event(
        payload, sig_header, settings.stripe_webhook_secret
    )
