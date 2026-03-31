import asyncio
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    selectinload,
    Mapped,
    mapped_column,
)
from sqlalchemy import select, func


# оголошення базового класу у сучасному стилі
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)

    addresses: Mapped[list["Address"]] = relationship(
        "Address", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship("User", back_populates="addresses")

    def __repr__(self) -> str:
        return f"Address(id={self.id}, email='{self.email}')"


# створення асинхронного двигуна
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

# створення фабрики асинхронних сесій із збереженням атрибутів після коміту
async_session = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


# ініціалізація бази даних: видалення старих таблиць і створення нових, а також початкове заповнення даними
async def init_db():
    async with engine.begin() as conn:
        # видаляємо існуючі таблиці та створюємо нові
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        async with session.begin():
            # створення користувачів
            user1 = User(name="Іван Петренко", email="ivan@example.com")
            user2 = User(name="Марія Шевченко", email="maria@example.com")
            session.add_all([user1, user2])
            # await session.commit()

            # створення адрес та встановлення зв'язків з користувачами
            address1 = Address(email="ivan.work@example.com", user=user1)
            address2 = Address(email="ivan.personal@example.com", user=user1)
            address3 = Address(email="maria.work@example.com", user=user2)
            session.add_all([address1, address2, address3])

    print("База даних ініціалізована")


# CRUD операції


# створення користувача
async def create_user(name, email):
    async with async_session() as session:
        async with session.begin():
            user = User(name=name, email=email)
            session.add(user)
        # повторно запитуємо об'єкт, щоб отримати його id
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalars().first()
        return user


# читання всіх користувачів
async def get_all_users():
    async with async_session() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()
        return users


# отримання користувача за id
async def get_user_by_id(user_id):
    async with async_session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        return user


# отримання користувачів з адресами з використанням eager loading для запобігання DetachedInstanceError
async def get_users_with_addresses():
    async with async_session() as session:
        # за допомогою опції selectinload забезпечуємо попереднє завантаження адрес
        stmt = select(User).options(selectinload(User.addresses))
        result = await session.execute(stmt)
        users = result.scalars().all()
        return users


# оновлення даних користувача
async def update_user(user_id, name=None, email=None):
    async with async_session() as session:
        async with session.begin():
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if not user:
                return None

            if name:
                user.name = name
            if email:
                user.email = email

            return user


# видалення користувача
async def delete_user(user_id):
    async with async_session() as session:
        # async with session.begin():
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            return False

        await session.delete(user)
        await session.commit()
        return True


async def perform_queries():
    async with async_session() as session:
        print("\nЗапити ")

        # Запит з фільтрацією
        stmt = select(User).where(User.name.like("Іван%"))
        result = await session.execute(stmt)
        filtered_users = result.scalars().all()
        print("\nКористувачі, імена яких починаються на 'Іван':")
        for user in filtered_users:
            print(user)

        # Запит з JOIN
        stmt = select(User, Address).join(Address)
        result = await session.execute(stmt)
        # Результат містить кортежі (user, address)
        user_addresses = result.all()
        print("\nКористувачі та їх адреси:")
        for user, address in user_addresses:
            print(f"Користувач: {user}, Адреса: {address}")

        # Агрегатні функції
        stmt = select(func.count(User.id))
        result = await session.execute(stmt)
        count = result.scalar()
        print(f"\nКількість користувачів: {count}")


# основна функція для демонстрації роботи CRUD операцій
async def main():
    await init_db()

    # виводимо всіх користувачів
    users = await get_all_users()
    print("\nВсі користувачі:")
    for user in users:
        print(user)

    print("\nВсі користувачі у форматі dict:")
    columns = ["id", "name", "email"]
    result = [dict(zip(columns, (row.id, row.name, row.email))) for row in users]
    print(result)

    # створення нового користувача
    new_user = await create_user("Петро Іваненко", "petro@example.com")
    print(f"\nСтворено нового користувача: {new_user}")

    # оновлення даних користувача
    updated_user = await update_user(new_user.id, name="Петро Оновлений")
    print(f"\nОновлено користувача: {updated_user}")

    # отримання користувачів разом з адресами
    users_with_addresses = await get_users_with_addresses()
    print("\nКористувачі з адресами:")
    for user in users_with_addresses:
        print(f"{user.name}:")
        for address in user.addresses:
            print(f"  — {address.email}")

    # видалення користувача
    deleted = await delete_user(new_user.id)
    print(f"\nВидалення користувача: {'успішно' if deleted else 'не вдалося'}")

    # перевірка залишених користувачів
    remaining_users = await get_all_users()
    print("\nКористувачі після видалення:")
    for user in remaining_users:
        print(user)

    await perform_queries()


if __name__ == "__main__":
    asyncio.run(main())
