"""Live demo setup: make sure the demo staff account exists (hosts like Render have no shell)."""

import secrets

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.core.settings import settings
from app.models import User


def ensure_demo_user() -> None:
    """Create the DEMO_EMAIL account if it's missing. Its password is random and never shown:
    the only way in is the one-click demo login, which DEMO_EMAIL also switches on."""
    email = settings.demo_email.strip().lower()
    if not email:
        return
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)) is None:
            password = hash_password(secrets.token_urlsafe(32))
            db.add(User(name="Demo Staff", email=email, password_hash=password))
            db.commit()


if __name__ == "__main__":
    ensure_demo_user()
