from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.schemas.auth import UserCreate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, username: str, email: str) -> User | None:
        stmt = select(User).where(or_(User.username == username, User.email == email))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, body: UserCreate, password_hash: str) -> User:
        user = User(
            username=body.username,
            email=str(body.email),
            password_hash=password_hash,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
