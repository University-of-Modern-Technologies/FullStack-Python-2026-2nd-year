"""Заповнення БД тестовими даними (перезаписуємо всі рядки)."""

from datetime import date

from sqlalchemy import delete

from db_connect import SessionLocal
from entity.models import Contact, Student, Teacher


def clear_all(session) -> None:
    session.execute(delete(Contact))
    session.execute(delete(Student))
    session.execute(delete(Teacher))
    session.commit()


def seed(session) -> None:
    teachers = [
        Teacher(
            id=1,
            first_name="Анна",
            last_name="Коваленко",
            email="anna@example.com",
            phone="+380501111111",
            address="Київ",
            start_work=date(2015, 9, 1),
        ),
        Teacher(
            id=2,
            first_name="Борис",
            last_name="Мельник",
            email="boris@example.com",
            phone="+380502222222",
            address="Львів",
            start_work=date(2022, 1, 10),
        ),
        Teacher(
            id=3,
            first_name="Віра",
            last_name="Шевченко",
            email="vira@example.com",
            phone="+380503333333",
            address="Одеса",
            start_work=date(2019, 5, 20),
        ),
        Teacher(
            id=4,
            first_name="Григорій",
            last_name="БезУчнів",
            email="solo@example.com",
            phone="+380504444444",
            address="Харків",
            start_work=date(2020, 6, 1),
        ),
    ]
    students = [
        Student(
            id=1,
            first_name="Олена",
            last_name="Петренко",
            email="olena@example.com",
            phone="+380611111111",
            address="Київ",
        ),
        Student(
            id=2,
            first_name="Максим",
            last_name="Іваненко",
            email="max@example.com",
            phone="+380622222222",
            address="Київ",
        ),
        Student(
            id=3,
            first_name="Катерина",
            last_name="Сидоренко",
            email="katya@example.com",
            phone="+380633333333",
            address="Львів",
        ),
        Student(
            id=4,
            first_name="Дмитро",
            last_name="Кравченко",
            email="dima@example.com",
            phone="+380644444444",
            address="Одеса",
        ),
        Student(
            id=5,
            first_name="Юлія",
            last_name="Мороз",
            email="yulia@example.com",
            phone="+380655555555",
            address="Вінниця",
        ),
        Student(
            id=6,
            first_name="Андрій",
            last_name="Лисенко",
            email="andriy@example.com",
            phone="+380666666666",
            address="Полтава",
        ),
        Student(
            id=7,
            first_name="Наталія",
            last_name="Ткаченко",
            email="nata@example.com",
            phone="+380677777777",
            address="Суми",
        ),
        Student(
            id=8,
            first_name="Ігор",
            last_name="Романенко",
            email="igor@example.com",
            phone="+380688888888",
            address="Чернігів",
        ),
        Student(
            id=9,
            first_name="Світлана",
            last_name="Гончар",
            email="svit@example.com",
            phone="+380699999999",
            address="Житомир",
        ),
        Student(
            id=10,
            first_name="Павло",
            last_name="БезКонтактів",
            email="pavlo@example.com",
            phone="+380600000010",
            address="Рівне",
        ),
    ]
    session.add_all(teachers)
    session.add_all(students)
    session.flush()

    s_map = {s.id: s for s in students}
    t_map = {t.id: t for t in teachers}

    s_map[1].teachers.extend([t_map[1], t_map[2]])
    s_map[2].teachers.append(t_map[1])
    s_map[3].teachers.extend([t_map[2], t_map[3]])
    s_map[4].teachers.append(t_map[3])
    s_map[5].teachers.append(t_map[1])
    s_map[6].teachers.append(t_map[2])
    s_map[7].teachers.append(t_map[1])
    s_map[8].teachers.append(t_map[2])
    s_map[9].teachers.append(t_map[1])
    s_map[10].teachers.append(t_map[1])

    contacts = [
        Contact(
            first_name="Роман",
            last_name="Бондаренко",
            email="roman.bondarenko@example.com",
            phone="+380711111111",
            student_id=1,
        ),
        Contact(
            first_name="Леся",
            last_name="Кравчук",
            email="lesia.kravchuk@example.com",
            phone="+380722222222",
            student_id=1,
        ),
        Contact(
            first_name="Олег",
            last_name="Савченко",
            email="oleh.savchenko@example.com",
            phone="+380733333333",
            student_id=2,
        ),
        Contact(
            first_name="Марія",
            last_name="Поліщук",
            email="mariia.polischuk@example.com",
            phone="+380744444444",
            student_id=3,
        ),
        Contact(
            first_name="Василь",
            last_name="Тарасенко",
            email="vasyl.tarasenko@example.com",
            phone="+380755555555",
            student_id=7,
        ),
        Contact(
            first_name="Тетяна",
            last_name="Марченко",
            email="tetiana.marchenko@example.com",
            phone="+380766666666",
            student_id=8,
        ),
        Contact(
            first_name="Євген",
            last_name="Руденко",
            email="yevhen.rudenko@example.com",
            phone="+380777777777",
            student_id=9,
        ),
    ]
    session.add_all(contacts)
    session.commit()


def main() -> None:
    with SessionLocal() as session:
        clear_all(session)
        seed(session)
    print("OK: teachers 1–4, students 1–10, зв’язки та контакти записані.")


if __name__ == "__main__":
    main()
