from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User, UserRole
from src.repository.users import UserRepository


class UsersService:
    def __init__(self, db: AsyncSession):
        self.users = UserRepository(db)

    async def list_users(self) -> list[User]:
        return await self.users.list_users()

    async def update_role(self, user_id: int, role: UserRole) -> User | None:
        return await self.users.update_role(user_id, role)


async def get_users_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsersService:
    return UsersService(db)
