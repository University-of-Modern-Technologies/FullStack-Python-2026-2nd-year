"""Сервіс операцій над користувачами та профілем."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.constants import AVATAR_MAX_BYTES
from src.database.db import get_db
from src.entity.models import User, UserRole
from src.repository.users import UserRepository
from src.services.avatars import upload_avatar


class UsersService:
    """Координує операції профілю та адміністративні зміни користувачів."""
    def __init__(self, db: AsyncSession):
        """Ініціалізує екземпляр класу та його залежності."""
        self.users = UserRepository(db)

    async def list_users(self) -> list[User]:
        """Повертає список користувачів, відсортований за id."""
        return await self.users.list_users()

    async def update_role(self, user_id: int, role: UserRole) -> User | None:
        """Оновлює роль користувача і повертає оновлену модель."""
        return await self.users.update_role(user_id, role)

    async def update_avatar(self, user_id: int, file_bytes: bytes) -> User:
        """Завантажує аватар і зберігає URL у профілі користувача."""
        if len(file_bytes) > AVATAR_MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Avatar file is too large",
            )
        avatar_url = await upload_avatar(file_bytes, user_id)
        user = await self.users.update_avatar_url(user_id, avatar_url)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def get_me(self, user_id: int) -> User:
        """Повертає ORM-модель поточного користувача."""
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user


async def get_users_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsersService:
    """FastAPI dependency, що створює UsersService для запиту."""
    return UsersService(db)
