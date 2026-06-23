"""Репозиторій для збереження та пошуку refresh-токенів."""
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken


class RefreshTokenRepository:
    """Інкапсулює SQL-запити для refresh-токенів."""
    def __init__(self, session: AsyncSession):
        """Ініціалізує екземпляр класу та його залежності."""
        self.db = session

    async def create_token(
        self, user_id: int, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        """Виконує операцію create_token у модулі refresh_tokens."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)
        return refresh_token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Виконує операцію get_by_hash у модулі refresh_tokens."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_hash(self, token_hash: str) -> None:
        """Виконує операцію delete_by_hash у модулі refresh_tokens."""
        stmt = delete(RefreshToken).where(RefreshToken.token_hash == token_hash)
        await self.db.execute(stmt)
        await self.db.commit()
