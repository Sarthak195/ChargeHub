from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from database import get_db
from models.user import User, UserRole
from auth import hash_password, verify_password, create_access_token, get_current_user
import services.stripe_service as stripe_svc
from config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    unit_number: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    unit_number: str | None
    role: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check duplicate email
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        unit_number=body.unit_number,
        role=UserRole.resident,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create Stripe customer in background (best-effort)
    if settings.stripe_secret_key and not settings.stripe_secret_key.startswith("sk_test_placeholder"):
        try:
            stripe_id = await stripe_svc.get_or_create_stripe_customer(user.email, user.full_name)
            user.stripe_customer_id = stripe_id
            db.add(user)
            await db.commit()
        except Exception:
            pass  # Non-fatal

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
