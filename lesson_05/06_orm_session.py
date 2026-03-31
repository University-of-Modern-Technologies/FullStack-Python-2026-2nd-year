from sqlalchemy import create_engine, ForeignKey, Integer, String, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from contextlib import contextmanager

# Створення з'єднання та базової моделі
engine = create_engine("sqlite:///session_example.db", echo=False)


# Базовий клас для всіх моделей
class Base(DeclarativeBase):
    pass


# Визначення моделей
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    age: Mapped[int] = mapped_column(Integer)

    # Один користувач має багато адрес
    addresses: Mapped[list["Address"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"


class Address(Base):
    __tablename__ = 'addresses'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    # Багато адрес належать одному користувачу
    user: Mapped["User"] = relationship(back_populates="addresses")

    def __repr__(self):
        return f"Address(id={self.id}, email='{self.email}')"


# Додамо функцію налаштування бази даних
def setup_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("База даних успішно створена!")


# Фабрика сесій (не плутати з типом sqlalchemy.orm.Session)
SessionLocal = sessionmaker(bind=engine)


# Контекстний менеджер для сесій
@contextmanager
def session_scope():
    _session = SessionLocal()
    try:
        yield _session
        _session.commit()
    except Exception:
        _session.rollback()
        raise
    finally:
        _session.close()


# Функції для роботи з даними (сесію передаємо явно — зручно для тестів і імпорту)
def add_user(session: Session, name, email, age=None):
    # Спочатку перевіряємо, чи існує користувач з таким email
    existing_user = session.query(User).filter_by(email=email).first()
    if existing_user:
        print(f"Користувач з email {email} вже існує. Повертаємо існуючий ID.")
        return existing_user.id

    # Якщо користувач не існує, створюємо нового
    user = User(name=name, email=email, age=age)
    session.add(user)
    session.flush()  # Щоб отримати ID до коміту
    return user.id


def add_address(session: Session, user_id, email):
    user = session.get(User, user_id)
    if not user:
        raise ValueError(f"Користувача з ID {user_id} не знайдено")

    address = Address(email=email, user=user)
    session.add(address)
    session.flush()  # Щоб отримати ID до коміту
    return address.id


def update_user(session: Session, user_id, **kwargs):
    user = session.get(User, user_id)
    if not user:
        raise ValueError(f"Користувача з ID {user_id} не знайдено")

    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)

    return user


def delete_user(session: Session, user_id):
    user = session.get(User, user_id)
    if not user:
        raise ValueError(f"Користувача з ID {user_id} не знайдено")

    session.delete(user)


def get_all_users(session: Session):
    return session.query(User).all()


def get_users_with_addresses(session: Session):
    return session.query(User).join(Address).all()


def get_user_by_email(session: Session, email):
    return session.query(User).filter_by(email=email).first()


def get_users_by_age_range(session: Session, min_age, max_age):
    return session.query(User).filter(User.age >= min_age, User.age <= max_age).all()


def count_addresses_per_user(session: Session):
    result = session.query(
        User.name,
        func.count(Address.id).label('address_count')
    ).join(Address).group_by(User.name).all()

    return [(name, count) for name, count in result]


# Демонстрація використання
if __name__ == "__main__":
    # Спочатку налаштовуємо базу даних
    setup_database()
    with session_scope() as session:
        # Додавання користувачів
        user1_id = add_user(session, "Олександр", "oleksandr@example.com", 30)
        user2_id = add_user(session, "Марія", "maria@example.com", 25)
        user3_id = add_user(session, "Іван", "ivan@example.com", 35)

        # Додавання адрес
        add_address(session, user1_id, "oleksandr.work@example.com")
        add_address(session, user1_id, "oleksandr.personal@example.com")
        add_address(session, user2_id, "maria.work@example.com")

        # Оновлення користувача
        update_user(session, user1_id, name="Олександр Новий", age=31)

        # Отримання та виведення всіх користувачів
        users = get_all_users(session)
        print("\nВсі користувачі:")
        for user in users:
            # Виводимо тільки базову інформацію, щоб уникнути проблем з DetachedInstanceError
            print(f"Id: {user.id}, Ім'я: {user.name}, Email: {user.email}, Вік: {user.age}")

        # Отримання користувачів за критеріями
        users_by_age = get_users_by_age_range(session, 25, 32)
        print("\nКористувачі віком від 25 до 32:")
        for user in users_by_age:
            print(f"Id: {user.id}, Ім'я: {user.name}, Email: {user.email}, Вік: {user.age}")

        # Отримання користувачів з адресами
        users_with_addresses = get_users_with_addresses(session)
        print("\nКористувачі з адресами:")
        for user in users_with_addresses:
            print(f"{user.name} має адреси:")
            for address in user.addresses:
                print(f"  - {address.email}")

        # Підрахунок адрес для кожного користувача
        address_counts = count_addresses_per_user(session)
        print("\nКількість адрес для кожного користувача:")
        for name, count in address_counts:
            print(f"{name}: {count} адрес")

        # Видалення користувача
        delete_user(session, user3_id)

        # Перевірка, що користувач видалений
        remaining_users = get_all_users(session)
        print("\nКористувачі після видалення:")
        for user in remaining_users:
            print(f"Id: {user.id}, Ім'я: {user.name}, Email: {user.email}, Вік: {user.age}")
