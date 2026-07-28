from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "development-only"
    database_url: str = "sqlite:///./crm_fuel.db"
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_enabled: bool = False
    rate_limit_read_per_minute: int = 120
    rate_limit_write_per_minute: int = 30
    telegram_bot_token: str = ""
    owner_telegram_id: int | None = None
    dev_auth_enabled: bool = True
    dev_user_id: int = 1
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    def validate_runtime(self) -> None:
        if self.app_env != "production":
            return
        errors = []
        if self.dev_auth_enabled:
            errors.append("DEV_AUTH_ENABLED must be false in production")
        if not self.telegram_bot_token:
            errors.append("TELEGRAM_BOT_TOKEN is required in production")
        if not self.owner_telegram_id:
            errors.append("OWNER_TELEGRAM_ID is required in production")
        if not self.rate_limit_enabled:
            errors.append("RATE_LIMIT_ENABLED must be true in production")
        if not self.redis_url:
            errors.append("REDIS_URL is required in production")
        if self.rate_limit_read_per_minute < 1 or self.rate_limit_write_per_minute < 1:
            errors.append("Rate limits must be positive")
        if "*" in self.allowed_origins or not self.allowed_origins:
            errors.append("CORS_ORIGINS must contain explicit trusted origins")
        if self.secret_key == "development-only" or len(self.secret_key) < 32:
            errors.append("SECRET_KEY must contain at least 32 non-default characters")
        if errors:
            raise RuntimeError("; ".join(errors))


@lru_cache
def get_settings() -> Settings:
    return Settings()
