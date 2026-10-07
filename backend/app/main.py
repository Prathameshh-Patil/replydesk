"""The FastAPI application: creates the app and plugs in the routes."""

from fastapi import FastAPI

from app.core.settings import settings

app = FastAPI(title="ReplyDesk API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Lets Docker, CI and the hosting platform check that the API is up."""
    return {"status": "ok", "environment": settings.environment}
