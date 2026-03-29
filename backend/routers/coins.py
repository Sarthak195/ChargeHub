"""
Coin wallet router — balance, transaction history, and Stripe top-up.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.user import User
from models.coin_transaction import CoinTransaction, CoinTxType
from auth import get_current_user, require_admin
import services.stripe_service as stripe_svc
from config import get_settings

router = APIRouter(prefix="/api/coins", tags=["coins"])
settings = get_settings()


class CoinBalanceResponse(BaseModel):
    coin_balance: float
    coins_per_kwh: float
    coins_per_minute: float
    coin_topup_rate_usd: float   # USD per coin


class CoinTxResponse(BaseModel):
    id: int
    amount: float
    tx_type: str
    description: Optional[str]
    balance_after: float
    created_at: str

    model_config = {"from_attributes": True}


class TopupRequest(BaseModel):
    coins: int   # how many coins to buy (min 10)


class TopupResponse(BaseModel):
    client_secret: str
    stripe_publishable_key: str
    coins: int
    amount_usd: float


class AdminCreditRequest(BaseModel):
    user_id: int
    coins: float
    reason: str


@router.get("/balance", response_model=CoinBalanceResponse)
async def get_balance(user: User = Depends(get_current_user)):
    return CoinBalanceResponse(
        coin_balance=user.coin_balance,
        coins_per_kwh=settings.coins_per_kwh,
        coins_per_minute=settings.coins_per_minute,
        coin_topup_rate_usd=settings.coin_topup_rate,
    )


@router.get("/transactions", response_model=list[CoinTxResponse])
async def get_transactions(
    limit: int = 30,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CoinTransaction)
        .where(CoinTransaction.user_id == user.id)
        .order_by(desc(CoinTransaction.created_at))
        .limit(limit)
        .offset(offset)
    )
    txs = result.scalars().all()
    return [
        CoinTxResponse(
            id=tx.id,
            amount=tx.amount,
            tx_type=tx.tx_type.value,
            description=tx.description,
            balance_after=tx.balance_after,
            created_at=tx.created_at.isoformat(),
        )
        for tx in txs
    ]


@router.post("/topup", response_model=TopupResponse)
async def topup_coins(
    body: TopupRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a Stripe PaymentIntent to purchase coins."""
    if body.coins < 10:
        raise HTTPException(400, "Minimum top-up is 10 coins")

    amount_usd = round(body.coins * settings.coin_topup_rate, 2)
    amount_cents = int(amount_usd * 100)

    if not user.stripe_customer_id:
        cid = await stripe_svc.get_or_create_stripe_customer(user.email, user.full_name)
        user.stripe_customer_id = cid
        db.add(user)
        await db.commit()

    import stripe
    stripe.api_key = settings.stripe_secret_key
    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency="usd",
        customer=user.stripe_customer_id,
        metadata={
            "chargehub_topup": "true",
            "user_id": str(user.id),
            "coins": str(body.coins),
        },
    )
    return TopupResponse(
        client_secret=intent.client_secret,
        stripe_publishable_key=settings.stripe_publishable_key,
        coins=body.coins,
        amount_usd=amount_usd,
    )


@router.post("/admin/credit")
async def admin_credit(
    body: AdminCreditRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin manually credits coins to a resident (e.g., for cash payment or promo)."""
    target_user = await db.get(User, body.user_id)
    if not target_user:
        raise HTTPException(404, "User not found")

    target_user.coin_balance = round(target_user.coin_balance + body.coins, 2)
    db.add(target_user)

    tx = CoinTransaction(
        user_id=body.user_id,
        amount=body.coins,
        tx_type=CoinTxType.admin_credit,
        description=body.reason,
        balance_after=target_user.coin_balance,
    )
    db.add(tx)
    await db.commit()

    return {"user_id": body.user_id, "coins_credited": body.coins, "new_balance": target_user.coin_balance}
