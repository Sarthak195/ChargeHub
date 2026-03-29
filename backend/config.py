from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://chargehub:chargehubpass@localhost:5432/chargehub"

    # Security
    secret_key: str = "dev_secret"
    access_token_expire_minutes: int = 60

    # Tapo
    tapo_username: str = ""
    tapo_password: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    # Coin System
    coins_per_kwh: float = 10.0        # coins deducted per kWh consumed
    coins_per_minute: float = 0.5      # coins deducted per minute of session time
    coin_topup_rate: float = 0.10      # USD per coin (for Stripe top-up)

    # App
    poll_interval_seconds: int = 30
    app_env: str = "development"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
