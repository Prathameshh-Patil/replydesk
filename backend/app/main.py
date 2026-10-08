"""The FastAPI application: creates the app and plugs in the routes."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.routers import auth, stats, tickets

app = FastAPI(title="ReplyDesk API", version="0.1.0")

# Browsers block a page on one address from calling an API on another unless the API allows it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(stats.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Lets Docker, CI and the hosting platform check that the API is up."""
    return {"status": "ok", "environment": settings.environment}
