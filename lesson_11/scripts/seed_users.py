"""Тема 10: тестові користувачі для RBAC.

uv run python scripts/seed_users.py
Логіни: user_demo, mod_demo, admin_demo — пароль demo1234
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from src.database.db import sessionmanager
from src.entity.models import User, UserRole
from src.services.auth import hash_password

SEED_USERS = [
    ("user_demo", "user@example.com", UserRole.USER),
    ("mod_demo", "mod@example.com", UserRole.MODERATOR),
    ("admin_demo", "admin@example.com", UserRole.ADMIN),
]
PASSWORD = "demo1234"


async def seed() -> None:
    async with sessionmanager.session() as db:
        for username, email, role in SEED_USERS:
            result = await db.execute(select(User).where(User.username == username))
            existing = result.scalar_one_or_none()
            if existing:
                if existing.email != email:
                    existing.email = email
                    await db.commit()
                    print(f"updated email: {username}")
                else:
                    print(f"skip: {username}")
                continue
            user = User(
                username=username,
                email=email,
                password_hash=hash_password(PASSWORD),
                role=role,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"created: {username} ({role.value})")


if __name__ == "__main__":
    asyncio.run(seed())
