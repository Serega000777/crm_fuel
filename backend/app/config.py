from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "development-only"
    database_url: str = "sqlite:///./crm_fuel.db"
    redis_url: str = "redis://localhost:6379/0"
    telegram_bot_token: str = ""
    dev_auth_enabled: bool = True
    dev_user_id: int = 1
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

