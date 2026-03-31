from datetime import datetime

from sqlalchemy import (
    create_engine,
    ForeignKey,
    String,
    Integer,
    Table,
    Column,
    DateTime,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)


# Створення базового класу
class Base(DeclarativeBase):
    pass


# Таблиця для зв'язку багато-до-багатьох
teacher_student = Table(
    "teacher_student",
    Base.metadata,
    Column(
        "teacher_id",
        Integer,
        ForeignKey("teachers.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "student_id",
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# Модель вчителя
class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str] = mapped_column(String(100))
    start_work: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Зв'язок: багато-до-багатьох
    students: Mapped[list["Student"]] = relationship(
        secondary=teacher_student, back_populates="teachers"
    )

    def __repr__(self) -> str:
        return f"Teacher(id={self.id}, fullname='{self.fullname}')"


# Модель студента
class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str] = mapped_column(String(100))

    # Зв'язки
    teachers: Mapped[list["Teacher"]] = relationship(
        secondary=teacher_student, back_populates="students"
    )

    contacts: Mapped[list["Contact"]] = relationship(back_populates="student")

    profile: Mapped["StudentProfile"] = relationship(
        back_populates="student", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Student(id={self.id}, fullname='{self.fullname}')"


# Модель контакту
class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))

    # Зв'язок: багато-до-одного
    student: Mapped["Student"] = relationship(back_populates="contacts")

    def __repr__(self) -> str:
        return f"Contact(id={self.id}, fullname='{self.fullname}')"


# Модель профілю студента (один-до-одного з Student)
class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    bio: Mapped[str | None] = mapped_column(String(500))
    address: Mapped[str | None] = mapped_column(String(200))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))

    # Зв'язок: один-до-одного
    student: Mapped["Student"] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"StudentProfile(id={self.id}, student_id={self.student_id})"


# Створення двигуна та сесії
engine = create_engine("sqlite:///school.db", echo=False)
SessionLocal = sessionmaker(bind=engine)


# Функція налаштування бази даних
def setup_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("База даних успішно створена!")


# Функція заповнення бази даних тестовими даними
def seed_database():
    session = SessionLocal()
    try:
        # Створення вчителів
        teacher1 = Teacher(fullname="Ірина Петрівна")
        teacher2 = Teacher(fullname="Василь Іванович")
        teacher3 = Teacher(fullname="Марія Степанівна")

        # Створення студентів
        student1 = Student(fullname="Олександр Сидоренко")
        student2 = Student(fullname="Марія Коваленко")
        student3 = Student(fullname="Петро Шевченко")

        # Зв'язуємо вчителів зі студентами
        teacher1.students = [student1, student2]
        teacher2.students = [student1, student3]
        teacher3.students = [student2, student3]

        # Створення профілів студентів
        profile1 = StudentProfile(
            bio="Активний студент", address="м. Київ", student=student1
        )
        profile2 = StudentProfile(
            bio="Відмінниця", address="м. Львів", student=student2
        )
        profile3 = StudentProfile(
            bio="Спортсмен", address="м. Харків", student=student3
        )

        # Створення контактів
        contact1 = Contact(
            fullname="Мама Олександра", phone="+380991234567", student=student1
        )
        contact2 = Contact(
            fullname="Тато Олександра", phone="+380991234568", student=student1
        )
        contact3 = Contact(
            fullname="Тато Марії", phone="+380991234569", student=student2
        )

        # Додаємо всі до сесії та коміт
        session.add_all(
            [
                teacher1,
                teacher2,
                teacher3,
                student1,
                student2,
                student3,
                profile1,
                profile2,
                profile3,
                contact1,
                contact2,
                contact3,
            ]
        )
        session.commit()
        print("База даних успішно заповнена тестовими даними!")
    except Exception as e:
        session.rollback()
        print(f"Помилка при заповненні бази даних: {e}")
    finally:
        session.close()


# Приклади роботи з сесіями
def demonstrate_queries():
    # Створюємо сесію
    session = SessionLocal()
    try:
        # 1. Отримання всіх вчителів та їхніх студентів
        print("\n1. Всі вчителі та їхні студенти:")
        teachers = session.query(Teacher).all()
        for teacher in teachers:
            print(f"{teacher.fullname}:")
            for student in teacher.students:
                print(f"  - {student.fullname}")

        # 2. Отримання всіх студентів та їхніх вчителів
        print("\n2. Всі студенти та їхні вчителі:")
        students = session.query(Student).all()
        for student in students:
            print(f"{student.fullname}:")
            print(f"  Вчителі: {', '.join([t.fullname for t in student.teachers])}")

        # 3. Отримання профілів студентів
        print("\n3. Профілі студентів:")
        students = session.query(Student).all()
        for student in students:
            print(f"{student.fullname}:")
            print(f"  Біографія: {student.profile.bio}")
            print(f"  Адреса: {student.profile.address}")

        # 4. Отримання контактів студентів
        print("\n4. Контакти студентів:")
        students = session.query(Student).all()
        for student in students:
            print(f"{student.fullname}:")
            if student.contacts:
                for contact in student.contacts:
                    print(f"  - {contact.fullname}, тел: {contact.phone}")
            else:
                print("  Контакти відсутні")

        # 5. Пошук студента за іменем
        print("\n5. Пошук студента 'Марія Коваленко':")
        student = session.query(Student).filter_by(fullname="Марія Коваленко").first()
        if student:
            print(f"Знайдено: {student.fullname}")
            print(f"Вчителі: {', '.join([t.fullname for t in student.teachers])}")
            print(f"Профіль: {student.profile.bio}")
            print(f"Контакти: {', '.join([c.fullname for c in student.contacts])}")

        # 6. Пошук всіх студентів конкретного вчителя
        print("\n6. Всі студенти вчителя 'Василь Іванович':")
        teacher = session.query(Teacher).filter_by(fullname="Василь Іванович").first()
        if teacher:
            print(f"Студенти {teacher.fullname}:")
            for student in teacher.students:
                print(f"  - {student.fullname}")
    finally:
        session.close()


# Демонстрація операцій з відношеннями
def demonstrate_relationships():
    session = SessionLocal()
    try:
        print("\n7. Демонстрація роботи з відношеннями в коді:")

        # Додаємо нового студента
        new_student = Student(fullname="Ірина Мельник")

        # Додаємо профіль
        new_profile = StudentProfile(bio="Новий студент", address="м. Одеса")
        new_student.profile = new_profile

        # Додаємо контакт
        new_contact = Contact(fullname="Мама Ірини", phone="+380991234570")
        new_student.contacts.append(new_contact)

        # Зв'язуємо з існуючим вчителем
        teacher = session.query(Teacher).first()
        new_student.teachers.append(teacher)

        # Зберігаємо зміни
        session.add(new_student)
        session.commit()

        # Перевіряємо додавання
        added_student = (
            session.query(Student).filter_by(fullname="Ірина Мельник").first()
        )
        print(f"Доданий студент: {added_student.fullname}")
        print(f"Профіль: {added_student.profile.bio}")
        print(f"Контакти: {', '.join([c.fullname for c in added_student.contacts])}")
        print(f"Вчителі: {', '.join([t.fullname for t in added_student.teachers])}")

        # Модифікуємо зв'язки
        print("\n8. Модифікація зв'язків:")

        # Додаємо ще одного вчителя
        second_teacher = (
            session.query(Teacher).filter_by(fullname="Марія Степанівна").first()
        )
        added_student.teachers.append(second_teacher)

        # Оновлюємо профіль
        added_student.profile.bio = "Оновлена біографія"

        # Додаємо ще один контакт
        another_contact = Contact(fullname="Тато Ірини", phone="+380991234571")
        added_student.contacts.append(another_contact)

        # Зберігаємо зміни
        session.commit()

        # Перевіряємо оновлення
        updated_student = (
            session.query(Student).filter_by(fullname="Ірина Мельник").first()
        )
        print(f"Оновлений студент: {updated_student.fullname}")
        print(f"Оновлений профіль: {updated_student.profile.bio}")
        print(f"Контакти: {', '.join([c.fullname for c in updated_student.contacts])}")
        print(f"Вчителі: {', '.join([t.fullname for t in updated_student.teachers])}")

        # Додаткові приклади запитів з використанням сесії
        print("\n9. Приклади розширених запитів:")

        # Фільтрація по віку
        print("\nСтуденти вчителя Василь Іванович з додатковою фільтрацією:")
        teacher_students = (
            session.query(Student)
            .join(Student.teachers)
            .filter(Teacher.fullname == "Василь Іванович")
            .all()
        )
        for student in teacher_students:
            print(f"  - {student.fullname}")

        # Підрахунок кількості студентів у кожного вчителя
        print("\nКількість студентів у кожного вчителя:")
        for teacher in session.query(Teacher).all():
            print(f"{teacher.fullname}: {len(teacher.students)} студентів")
    except Exception as e:
        session.rollback()
        print(f"Помилка: {e}")
    finally:
        session.close()


def main():
    setup_database()
    seed_database()
    demonstrate_queries()
    demonstrate_relationships()


if __name__ == "__main__":
    main()
