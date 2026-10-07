"""Create a staff login from the command line (there is deliberately no public sign-up).

Usage: python -m app.create_user "Asha Kulkarni" asha@example.com 'a-strong-password'
"""

import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    name, email, password = sys.argv[1], sys.argv[2].strip().lower(), sys.argv[3]
    if len(password) < 8:
        sys.exit("Password must be at least 8 characters")
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            sys.exit(f"A user with email {email} already exists")
        db.add(User(name=name, email=email, password_hash=hash_password(password)))
        db.commit()
    print(f"Created user {email}")


if __name__ == "__main__":
    main()
