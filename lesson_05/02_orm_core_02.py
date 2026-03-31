# вирази SELECT

from sqlalchemy import Table, Column, Integer, Boolean, String, MetaData, create_engine
from sqlalchemy.sql import select, and_, or_, not_, func

metadata = MetaData()
engine = create_engine("sqlite:///:memory:", echo=False)


users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fullname", String),
    Column("age", Integer),
    Column("active", Boolean),
)

metadata.create_all(engine)

if __name__ == "__main__":
    with engine.connect() as conn:
        conn.execute(
            users.insert(),
            [
                {"fullname": "Jack Jones", "age": 37, "active": 1},
                {"fullname": "Vasya Pupkin", "age": 25, "active": 1},
                {"fullname": "Ivan Petrov", "age": 45, "active": 0},
                {"fullname": "Mykola Shevchenko", "age": 30, "active": 1},
                {"fullname": "Olena Kovalenko", "age": 22, "active": 1},
            ],
        )

        # Базова фільтрація
        stmt = select(users).where(users.c.age > 30)
        print("\nКористувачі, старші за 30 років:")
        for row in conn.execute(stmt):
            print(f"ID: {row.id}, Name: {row.fullname}, Age: {row.age}")

        # Складна фільтрація з операторами AND, OR, NOT
        stmt = select(users).where(and_(users.c.age > 25, users.c.active == 1))
        print("\nАктивні користувачі, старші за 25 років:")
        for row in conn.execute(stmt):
            print(f"ID: {row.id}, Name: {row.fullname}, Age: {row.age}")

        # Використання OR
        stmt = select(users).where(or_(users.c.age < 25, users.c.age > 40))
        print("\nКористувачі молодші за 25 або старші за 40 років:")
        for row in conn.execute(stmt):
            print(f"ID: {row.id}, Name: {row.fullname}, Age: {row.age}")

        # Використання NOT
        stmt = select(users).where(not_(users.c.active == 1))
        print("\nНеактивні користувачі:")
        for row in conn.execute(stmt):
            print(f"ID: {row.id}, Name: {row.fullname}, Age: {row.age}")

        # Комбінація NOT з іншими операторами
        stmt = select(users).where(
            and_(
                not_(users.c.age < 30),  # Вік не менше 30
                not_(users.c.active == 0),  # Активний
            )
        )
        print("\nАктивні користувачі віком від 30 років:")
        for row in conn.execute(stmt):
            print(f"ID: {row.id}, Name: {row.fullname}, Age: {row.age}")

        # Інший спосіб використання NOT
        stmt = select(users).where(not_(or_(users.c.age <= 25, users.c.active == 0)))
        print("\nАктивні користувачі старші за 25 років (використання NOT з OR):")
        for row in conn.execute(stmt):
            print(f"ID: {row.id}, Name: {row.fullname}, Age: {row.age}")

        # Використання агрегатних функцій
        stmt = select(func.count(users.c.id))
        count = conn.execute(stmt).scalar()
        print(f"\nЗагальна кількість користувачів: {count}")

        # Обчислення середнього віку
        stmt = select(func.avg(users.c.age))
        avg_age = conn.execute(stmt).scalar()
        print(f"Середній вік користувачів: {avg_age:.1f}")

        # Групування та агрегація
        stmt = select(users.c.active, func.count(users.c.id)).group_by(users.c.active)
        print("\nСтатистика за статусом активності:")
        for active, count in conn.execute(stmt):
            status = "активних" if active else "неактивних"
            print(f"Кількість {status} користувачів: {count}")

        # Сортування результатів
        stmt = select(users).order_by(users.c.age.desc())
        print("\nКористувачі за віком (спадання):")
        for row in conn.execute(stmt):
            print(f"ID: {row.id}, Name: {row.fullname}, Age: {row.age}")
