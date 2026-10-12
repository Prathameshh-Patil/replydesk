"""All configuration, read from environment variables (or a .env file) in one place."""

from pathlib import Path
from typing import Literal

from pydantic import field_validator
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

    # Any OpenAI-compatible chat API. We use Groq; Gemini, Ollama, etc. work by changing these.
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: str = ""  # secret: set LLM_API_KEY in .env, never in code
    llm_model: str = "openai/gpt-oss-120b"
    llm_reasoning_effort: str = "low"
    llm_timeout_seconds: float = 60

    # Web addresses allowed to call the API from a browser (comma-separated): the front end.
    cors_origins: str = "http://localhost:3010"

    # Live demo only. Most new tickets per day (UTC), so visitors can't use up the model's free
    # quota; 0 means no limit.
    daily_ticket_limit: int = 0
    # Live demo only. If set, POST /auth/demo logs anyone in as this existing staff account
    # (the one-click demo login); empty means the endpoint is switched off.
    demo_email: str = ""

    # Folder with sorter.md, extractor.md, ... (repo-root/agents locally; set in the Docker image)
    agents_dir: Path = Path(__file__).resolve().parents[3] / "agents"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, url: str) -> str:
        """Hosted databases (Neon, Render) give postgresql:// URLs; SQLAlchemy needs the driver."""
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url


settings = Settings()

if settings.environment == "production" and (
    settings.jwt_secret.startswith("dev-only") or len(settings.jwt_secret) < 32
):
    raise RuntimeError("Set JWT_SECRET to a random value of at least 32 characters in production")
