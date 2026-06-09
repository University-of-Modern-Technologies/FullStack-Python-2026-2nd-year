"""Асинхронне підключення до PostgreSQL і FastAPI dependency для сесій."""
import contextlib
import logging

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import settings

logger = logging.getLogger("uvicorn.error")


class DatabaseSessionManager:
    """Керує async engine і життєвим циклом SQLAlchemy-сесій."""
    def __init__(self, url: str):
        """Ініціалізує екземпляр класу та його залежності."""
        self._engine: AsyncEngine = create_async_engine(url)
        self._session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            bind=self._engine,
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """Відкриває async DB-сесію і гарантує rollback/close при помилках."""
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            raise
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """FastAPI dependency, що надає async SQLAlchemy-сесію на час запиту."""
    async with sessionmanager.session() as session:
        yield session
