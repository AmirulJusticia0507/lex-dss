"""Create the first administrator without putting credentials in command history.

Run from backend/: python scripts/create_admin.py admin@example.org
"""

import asyncio
import getpass
import sys
from pathlib import Path

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import async_session_maker  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.user import User  # noqa: E402


async def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/create_admin.py ADMIN_EMAIL")
    try:
        email = TypeAdapter(EmailStr).validate_python(sys.argv[1])
    except ValidationError as exc:
        raise SystemExit("Enter a valid administrator email") from exc

    password = getpass.getpass("New administrator password (min. 8 chars): ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 8 or password != confirmation:
        raise SystemExit("Password must be at least 8 characters and both entries must match")

    async with async_session_maker() as session:
        existing = await session.scalar(select(User).where(User.email == str(email)))
        if existing:
            raise SystemExit("An account with that email already exists; use the admin account manager instead")
        admin = User(
            email=str(email),
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True,
            is_superuser=True,
        )
        session.add(admin)
        await session.commit()
    print(f"Administrator created: {email}")


if __name__ == "__main__":
    asyncio.run(main())
