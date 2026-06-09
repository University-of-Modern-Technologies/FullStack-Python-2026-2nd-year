"""Репозиторій SQL-операцій над користувачами."""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User, UserRole
from src.schemas.user import UserCreate


class UserRepository:
    """Інкапсулює SQL-запити для користувачів."""
    def __init__(self, session: AsyncSession):
        """Ініціалізує екземпляр класу та його залежності."""
        self.db = session

    async def get_by_id(self, user_id: int) -> User | None:
        """Виконує операцію get_by_id у модулі users."""
        return await self.db.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        """Виконує операцію get_by_username у модулі users."""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Виконує операцію get_by_email у модулі users."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, username: str, email: str) -> User | None:
        """Виконує операцію get_by_username_or_email у модулі users."""
        stmt = select(User).where(or_(User.username == username, User.email == email))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, body: UserCreate, password_hash: str) -> User:
        """Виконує операцію create_user у модулі users."""
        user = User(
            username=body.username,
            email=str(body.email),
            password_hash=password_hash,
            role=UserRole.USER,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def list_users(self) -> list[User]:
        """Повертає список користувачів, відсортований за id."""
        stmt = select(User).order_by(User.id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_role(self, user_id: int, role: UserRole) -> User | None:
        """Оновлює роль користувача і повертає оновлену модель."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.role = role
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def mark_email_verified(self, user_id: int) -> User | None:
        """Виконує операцію mark_email_verified у модулі users."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.email_verified = True
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_avatar_url(self, user_id: int, avatar_url: str) -> User | None:
        """Виконує операцію update_avatar_url у модулі users."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        return user
