# Транзакції на рівні Core

from sqlalchemy import Table, Column, Integer, String, MetaData, create_engine
from sqlalchemy.sql import select
import traceback

metadata = MetaData()
engine = create_engine("sqlite:///:memory:", echo=True)

# Визначення таблиці
accounts = Table('accounts', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('owner', String),
                 Column('balance', Integer)
                 )

metadata.create_all(engine)

# Додавання початкових даних
with engine.connect() as conn:
    conn.execute(accounts.insert(), [
        {'owner': 'Alice', 'balance': 1000},
        {'owner': 'Bob', 'balance': 500}
    ])
    conn.commit()


# Функція для переказу коштів
def transfer_money(from_account, to_account, amount):
    with engine.begin() as conn:  # Автоматичне керування транзакцією
        try:
            # Перевірка балансу відправника
            from_acc = conn.execute(
                select(accounts).where(accounts.c.owner == from_account)
            ).fetchone()

            if from_acc.balance < amount:
                raise ValueError(f"Недостатньо коштів на рахунку {from_account}")

            # Зменшення балансу відправника
            conn.execute(
                accounts.update()
                .where(accounts.c.owner == from_account)
                .values(balance=accounts.c.balance - amount)
            )

            # Збільшення балансу отримувача
            conn.execute(
                accounts.update()
                .where(accounts.c.owner == to_account)
                .values(balance=accounts.c.balance + amount)
            )

            # У разі успішного завершення транзакція буде підтверджена автоматично
            print(f"Успішно переказано {amount} від {from_account} до {to_account}")
        except Exception as e:
            # У разі помилки транзакція буде відкинута автоматично
            print(f"Помилка переказу: {str(e)}")
            traceback.print_exc()
            # Тут не потрібно викликати rollback() - engine.begin() робить це автоматично

if __name__ == '__main__':
    # Виведення початкового стану рахунків
    with engine.connect() as conn:
        result = conn.execute(select(accounts))
        print("Початковий стан рахунків:")
        for row in result:
            print(f"Власник: {row.owner}, Баланс: {row.balance}")

    # Успішний переказ
    transfer_money('Alice', 'Bob', 300)

    # Виведення проміжного стану рахунків
    with engine.connect() as conn:
        result = conn.execute(select(accounts))
        print("\nПроміжний стан рахунків:")
        for row in result:
            print(f"Власник: {row.owner}, Баланс: {row.balance}")

    # Спроба переказу з недостатнім балансом
    transfer_money('Bob', 'Alice', 1000)

    # Виведення кінцевого стану рахунків
    with engine.connect() as conn:
        result = conn.execute(select(accounts))
        print("\nКінцевий стан рахунків:")
        for row in result:
            print(f"Власник: {row.owner}, Баланс: {row.balance}")