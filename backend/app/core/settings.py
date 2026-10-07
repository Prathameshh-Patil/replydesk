"""All configuration, read from environment variables (or a .env file) in one place."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    database_url: str = "postgresql+psycopg://replydesk:replydesk@localhost:5442/replydesk"

    # Secret used to sign login tokens. Anyone who knows it can forge a login, so production
    # must set its own long random value.
    jwt_secret: str = "dev-only-secret-change-me-in-production-please"
    jwt_expire_minutes: int = 8 * 60  # one work shift


settings = Settings()

if settings.environment == "production" and (
    settings.jwt_secret.startswith("dev-only") or len(settings.jwt_secret) < 32
):
    raise RuntimeError("Set JWT_SECRET to a random value of at least 32 characters in production")
