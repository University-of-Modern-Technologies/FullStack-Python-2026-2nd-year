import asyncio
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from main import app
from src.database.db import get_db
from src.entity.models import Base, Todo, User, UserRole
from src.schemas.auth import CurrentUser
from src.services.auth import create_access_token, hash_password
from src.services.cache import cache_service


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)

TEST_PASSWORD = "12345678"
SEED_USERS = {
    "user": ("user_demo", "user@example.com", UserRole.USER),
    "moderator": ("mod_demo", "mod@example.com", UserRole.MODERATOR),
    "admin": ("admin_demo", "admin@example.com", UserRole.ADMIN),
    "unverified": ("mail_demo", "mail@example.com", UserRole.USER),
}


async def _reset_database() -> dict[str, User]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    seeded: dict[str, User] = {}
    async with TestingSessionLocal() as session:
        for key, (username, email, role) in SEED_USERS.items():
            user = User(
                username=username,
                email=email,
                password_hash=hash_password(TEST_PASSWORD),
                role=role,
                email_verified=key != "unverified",
            )
            session.add(user)
            seeded[key] = user
        await session.flush()

        session.add_all(
            [
                Todo(
                    user_id=seeded["user"].id,
                    title="User todo",
                    description="User task",
                    completed=False,
                ),
                Todo(
                    user_id=seeded["moderator"].id,
                    title="Moderator todo",
                    description="Moderator task",
                    completed=True,
                ),
            ]
        )
        await session.commit()

        for user in seeded.values():
            await session.refresh(user)
        return seeded


@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch: pytest.MonkeyPatch) -> None:
    async def get_json(_key: str):
        return None

    async def set_json(_key: str, _value, _ttl_seconds: int) -> None:
        return None

    async def invalidate_user_todos(_user_id: int) -> None:
        return None

    async def ping() -> bool:
        return True

    monkeypatch.setattr(cache_service, "get_json", get_json)
    monkeypatch.setattr(cache_service, "set_json", set_json)
    monkeypatch.setattr(cache_service, "invalidate_user_todos", invalidate_user_todos)
    monkeypatch.setattr(cache_service, "ping", ping)


@pytest.fixture()
def seeded_users() -> dict[str, User]:
    return asyncio.run(_reset_database())


@pytest.fixture()
def client(seeded_users: dict[str, User]):
    async def override_get_db() -> AsyncIterator:
        session = TestingSessionLocal()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(seeded_users: dict[str, User]):
    def _headers(user_key: str = "user") -> dict[str, str]:
        user = seeded_users[user_key]
        token = create_access_token(CurrentUser.model_validate(user))
        return {"Authorization": f"Bearer {token}"}

    return _headers
