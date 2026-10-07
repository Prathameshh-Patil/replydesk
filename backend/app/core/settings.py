"""All configuration, read from environment variables (or a .env file) in one place."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    database_url: str = "postgresql+psycopg://replydesk:replydesk@localhost:5442/replydesk"


settings = Settings()
