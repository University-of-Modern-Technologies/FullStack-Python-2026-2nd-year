from decimal import Decimal

from sqlalchemy import (
    create_engine, select, insert, update, and_, or_, func, text,
    ForeignKey, Date, Integer, String, Numeric
)
from sqlalchemy.orm import relationship, Session, DeclarativeBase, Mapped, mapped_column
from datetime import date

# Створення двигуна
engine = create_engine("sqlite:///modern_sqlalchemy.db", echo=False)

# Базовий клас для всіх моделей (сучасний синтаксис)
class Base(DeclarativeBase):
    pass

# Визначення моделі Department
class Department(Base):
    __tablename__ = 'departments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Відділ має багато працівників; cascade гарантує видалення orphan-записів
    employees: Mapped[list["Employee"]] = relationship(
        "Employee", back_populates="department", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Department(id={self.id}, name='{self.name}')"

# Визначення моделі Employee
class Employee(Base):
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))

    # Встановлення зв'язку з відділом
    department: Mapped["Department"] = relationship("Department", back_populates="employees")

    def __repr__(self) -> str:
        return f"Employee(id={self.id}, name='{self.name}', salary={self.salary})"

# Функція для скидання бази даних (видалення існуючих таблиць і створення нових)
def reset_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

# Функція для заповнення бази тестовими даними з обробкою помилок
def seed_database():
    reset_database()  # Скидання бази для чистого запуску
    with Session(engine) as session:
        try:
            # Додавання відділів
            dept_stmt = insert(Department).values([
                {"name": "Інженерія"},
                {"name": "Маркетинг"},
                {"name": "Продажі"},
                {"name": "Підтримка"}
            ])
            session.execute(dept_stmt)

            # Отримання ID відділів
            dept_id_map = {}
            for dept in session.execute(select(Department)).scalars():
                dept_id_map[dept.name] = dept.id

            # Додавання працівників
            emp_stmt = insert(Employee).values([
                {"name": "Іван Петренко", "hire_date": date(2019, 5, 15), "salary": 50000,
                 "department_id": dept_id_map["Інженерія"]},
                {"name": "Марія Коваленко", "hire_date": date(2020, 2, 10), "salary": 45000,
                 "department_id": dept_id_map["Інженерія"]},
                {"name": "Олександр Шевченко", "hire_date": date(2018, 10, 3), "salary": 55000,
                 "department_id": dept_id_map["Інженерія"]},
                {"name": "Наталія Іваненко", "hire_date": date(2021, 3, 22), "salary": 48000,
                 "department_id": dept_id_map["Маркетинг"]},
                {"name": "Василь Сидоренко", "hire_date": date(2017, 11, 8), "salary": 60000,
                 "department_id": dept_id_map["Маркетинг"]},
                {"name": "Олена Мельник", "hire_date": date(2019, 8, 14), "salary": 52000,
                 "department_id": dept_id_map["Продажі"]},
                {"name": "Максим Бондаренко", "hire_date": date(2020, 6, 5), "salary": 47000,
                 "department_id": dept_id_map["Продажі"]},
                {"name": "Юлія Ткаченко", "hire_date": date(2022, 1, 17), "salary": 42000,
                 "department_id": dept_id_map["Підтримка"]}
            ])
            session.execute(emp_stmt)
            session.commit()
            print("База даних успішно заповнена тестовими даними!")
        except Exception as e:
            session.rollback()
            print(f"Помилка при заповненні бази даних: {e}")

# Демонстрація різних запитів з використанням сучасного API з обробкою помилок
def demonstrate_queries():
    with Session(engine) as session:
        try:
            # 1. Базовий SELECT з фільтрацією
            print("\n1. Працівники з зарплатою понад 50000:")
            stmt = select(Employee).where(Employee.salary > 50000)
            result = session.execute(stmt)
            for employee in result.scalars():
                print(f"  {employee.name}: {employee.salary}")

            # 2. SELECT з JOIN та сортуванням
            print("\n2. Працівники з відділами, відсортовані за зарплатою:")
            stmt = select(Employee, Department).join(Department).order_by(Employee.salary.desc())
            result = session.execute(stmt)
            for employee, department in result:
                print(f"  {employee.name} ({department.name}): {employee.salary}")

            # 3. Агрегація даних з групуванням
            print("\n3. Середня зарплата по відділах:")
            stmt = select(
                Department.name,
                func.count(Employee.id).label("employee_count"),
                func.avg(Employee.salary).label("avg_salary")
            ).join(Department).group_by(Department.name)
            result = session.execute(stmt)
            for row in result:
                print(f"  {row.name}: {row.employee_count} працівників, середня зарплата {row.avg_salary:.2f}")

            # 4. Складна фільтрація з використанням AND та OR
            print("\n4. Складні умови фільтрації:")
            stmt = select(Employee).where(
                and_(
                    Employee.hire_date >= date(2019, 1, 1),
                    or_(
                        Employee.salary > 50000,
                        Employee.department_id == 1  # Інженерія
                    )
                )
            )
            result = session.execute(stmt)
            for employee in result.scalars():
                print(f"  {employee.name}: найнятий {employee.hire_date}, зарплата {employee.salary}")

            # 5. Підзапит – працівники з зарплатою вище середньої
            print("\n5. Працівники з зарплатою вище середньої:")
            subq = select(func.avg(Employee.salary)).scalar_subquery()
            stmt = select(Employee).where(Employee.salary > subq)
            result = session.execute(stmt)
            for employee in result.scalars():
                print(f"  {employee.name}: {employee.salary}")

            # 6. CTE для ранжування працівників за зарплатою
            print("\n6. Використання CTE для ранжування працівників за зарплатою:")
            salary_cte = select(
                Department.name.label("dept_name"),
                Employee.name.label("emp_name"),
                Employee.salary.label("salary"),
                func.rank().over(
                    partition_by=Department.name,
                    order_by=Employee.salary.desc()
                ).label("salary_rank")
            ).join(Department).cte("salary_ranks")
            stmt = select(salary_cte).where(salary_cte.c.salary_rank <= 2)
            result = session.execute(stmt)
            for row in result:
                print(f"  {row.dept_name}: {row.emp_name} (ранг {row.salary_rank}, зарплата {row.salary})")

            # 7. Оновлення даних (UPDATE)
            print("\n7. Оновлення зарплат для відділу підтримки:")
            update_stmt = update(Employee).where(
                Employee.department_id == 4  # Підтримка
            ).values(
                salary=Employee.salary * 1.1  # Збільшення на 10%
            )
            session.execute(update_stmt)
            session.commit()

            stmt = select(Employee).join(Department).where(Department.name == "Підтримка")
            result = session.execute(stmt)
            for employee in result.scalars():
                print(f"  {employee.name}: нова зарплата {employee.salary}")


            # 8. Виконання текстового SQL запиту
            print("\n8. Виконання текстового SQL запиту:")
            stmt = text("""
                SELECT e.name, e.salary, d.name as department
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                WHERE e.hire_date < :cutoff_date
                ORDER BY e.salary DESC
                LIMIT :limit
            """)
            result = session.execute(stmt, {"cutoff_date": date(2020, 1, 1), "limit": 4})
            for row in result:
                print(f"  {row.name}: {row.salary} ({row.department})")

        except Exception as e:
            session.rollback()
            print(f"Помилка під час виконання запитів: {e}")

if __name__ == "__main__":
    seed_database()
    demonstrate_queries()
