"""Seed the initial superadmin account.

Default credentials (matching lex-integrity):
  email:    superadmin@lex.local
  password: gedangbosok

Run: python scripts/seed_superadmin.py
"""
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import async_session_maker  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.user import User  # noqa: E402

SUPERADMIN_EMAIL = "superadmin@lex.local"
SUPERADMIN_PASSWORD = "gedangbosok"


async def main() -> None:
    async with async_session_maker() as session:
        existing = await session.scalar(
            select(User).where(User.email == SUPERADMIN_EMAIL)
        )
        if existing:
            print(f"Superadmin {SUPERADMIN_EMAIL} already exists (id={existing.id})")
            return
        user = User(
            email=SUPERADMIN_EMAIL,
            hashed_password=get_password_hash(SUPERADMIN_PASSWORD),
            full_name="Super Administrator",
            role="admin",
            institution="Lex DSS",
            is_active=True,
            is_superuser=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"Superadmin created: {user.email} (id={user.id}, role={user.role})")


if __name__ == "__main__":
    asyncio.run(main())