# Основні CRUD операції на рівні Core

from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
    MetaData,
    create_engine,
)
from sqlalchemy.sql import select

metadata = MetaData()
engine = create_engine("sqlite:///:memory:", echo=False)

# Визначення таблиць
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fullname", String),
)

addresses = Table(
    "addresses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id")),
)

metadata.create_all(engine)

if __name__ == "__main__":
    # Використання з'єднання для операцій з базою даних
    with engine.connect() as conn:
        # CREATE (INSERT) - додавання даних
        ins_user = users.insert().values(fullname="Jack Jones")
        print(str(ins_user))
        result = conn.execute(ins_user)
        jones_id = result.lastrowid  # Отримуємо ID доданого користувача

        # Додаємо ще одного користувача
        ins_user = users.insert().values(fullname="Vasya Pupkin")
        result = conn.execute(ins_user)
        pupkin_id = result.lastrowid

        # READ (SELECT) - отримання даних
        stmt = select(users)
        result = conn.execute(stmt)
        print("Користувачі:")
        for row in result:
            print(f"ID: {row.id}, Name: {row.fullname}")

        # INSERT для таблиці addresses
        ins_address = addresses.insert().values(
            email="jones@email.com", user_id=jones_id
        )
        conn.execute(ins_address)
        ins_address = addresses.insert().values(
            email="pupkin@email.com", user_id=pupkin_id
        )
        conn.execute(ins_address)

        # SELECT з таблиці addresses
        stmt = select(addresses)
        result = conn.execute(stmt)
        print("\nАдреси:")
        for row in result:
            print(f"ID: {row.id}, Email: {row.email}, User ID: {row.user_id}")

        # UPDATE - оновлення даних
        update_stmt = (
            users.update().where(users.c.id == jones_id).values(fullname="Jack Smith")
        )
        conn.execute(update_stmt)

        # DELETE - видалення даних
        delete_stmt = addresses.delete().where(addresses.c.user_id == pupkin_id)
        conn.execute(delete_stmt)

        # JOIN - об'єднання таблиць
        join_stmt = select(users.c.id, users.c.fullname, addresses.c.email).join(
            addresses
        )
        result = conn.execute(join_stmt)
        print("\nКористувачі з адресами:")
        for row in result:
            print(f"ID: {row.id}, Name: {row.fullname}, Email: {row.email}")
