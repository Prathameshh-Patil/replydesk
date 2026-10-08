"""All configuration, read from environment variables (or a .env file) in one place."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    database_url: str = "postgresql+psycopg://replydesk:replydesk@localhost:5442/replydesk"

    # Secret used to sign login tokens. Anyone who knows it can forge a login, so production
    # must set its own long random value.
    jwt_secret: str = "dev-only-secret-change-me-in-production-please"
    jwt_expire_minutes: int = 8 * 60  # one work shift

    # Which agent client to use: "llm" calls the model; "fake" gives canned answers (tests, demos).
    agent_client: Literal["llm", "fake"] = "llm"

    # Any OpenAI-compatible chat API: Ollama locally, Groq when deployed.
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"  # Ollama ignores it; Groq needs a real key
    llm_model: str = "gpt-oss:20b"
    llm_reasoning_effort: str = "low"
    llm_timeout_seconds: float = 180

    # Folder with sorter.md, extractor.md, ... (repo-root/agents locally; set in the Docker image)
    agents_dir: Path = Path(__file__).resolve().parents[3] / "agents"


settings = Settings()

if settings.environment == "production" and (
    settings.jwt_secret.startswith("dev-only") or len(settings.jwt_secret) < 32
):
    raise RuntimeError("Set JWT_SECRET to a random value of at least 32 characters in production")
