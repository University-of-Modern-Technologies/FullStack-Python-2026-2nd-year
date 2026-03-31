# Робота з текстовими SQL-запитами

from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String

metadata = MetaData()
engine = create_engine("sqlite:///:memory:", echo=True)

# Визначення таблиці
employees = Table('employees', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('name', String),
                  Column('department', String),
                  Column('salary', Integer)
                  )

metadata.create_all(engine)

if __name__ == '__main__':
    # Додавання тестових даних
    with engine.connect() as conn:
        conn.execute(employees.insert(), [
            {'name': 'Андрій', 'department': 'IT', 'salary': 50000},
            {'name': 'Марія', 'department': 'HR', 'salary': 45000},
            {'name': 'Петро', 'department': 'IT', 'salary': 60000},
            {'name': 'Оксана', 'department': 'Finance', 'salary': 55000},
            {'name': 'Олег', 'department': 'IT', 'salary': 70000}
        ])
        conn.commit()

    # Виконання текстового SQL-запиту
    with engine.connect() as conn:
        # Простий запит
        result = conn.execute(text("SELECT * FROM employees WHERE department = 'IT'"))
        print("Співробітники IT-відділу:")
        for row in result:
            print(f"ID: {row.id}, Ім'я: {row.name}, Зарплата: {row.salary}")

        # Запит з параметрами
        stmt = text("SELECT * FROM employees WHERE department = :dept AND salary > :min_salary")
        result = conn.execute(stmt, {"dept": "IT", "min_salary": 55000})
        print("\nВисокооплачувані співробітники IT-відділу:")
        for row in result:
            print(f"ID: {row.id}, Ім'я: {row.name}, Зарплата: {row.salary}")

        # Агрегація через текстовий запит
        stmt = text("""
            SELECT department, AVG(salary) as avg_salary, COUNT(*) as emp_count
            FROM employees
            GROUP BY department
            ORDER BY avg_salary DESC
        """)
        result = conn.execute(stmt)
        print("\nСтатистика по відділах:")
        for row in result:
            print(
                f"Відділ: {row.department}, Середня зарплата: {row.avg_salary:.2f}, Кількість співробітників: {row.emp_count}")