from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session, selectinload

from db_connect import SessionLocal
from entity.models import Contact, Student, Teacher, TeacherStudent


def _dump_val(v: Any) -> Any:
    if isinstance(v, datetime):
        return v.isoformat(sep=" ", timespec="seconds")
    if isinstance(v, date):
        return v.isoformat()
    return v


def _print_with_relation(
    rows: list[Any],
    rel_attr: str,
    *,
    extra_attrs: tuple[str, ...] = (),
) -> None:
    """Друкує об'єкти з id, fullname, додатковими полями та списком зв'язаних (id, fullname)."""
    for obj in rows:
        out = {"id": obj.id, "fullname": obj.fullname}
        for a in extra_attrs:
            out[a] = _dump_val(getattr(obj, a))
        related = sorted(getattr(obj, rel_attr), key=lambda x: x.id)
        out[rel_attr] = [(x.id, x.fullname) for x in related]
        print(out)


def get_student_join(session: Session) -> None:
    """Вибирає студентів, у яких є хоча б один учитель; учителів підвантажує selectinload.

    SQL (~):
        SELECT students.id, students.first_name, students.last_name, students.email,
               students.cell_phone, students.address, ...
        FROM students
        WHERE EXISTS (
            SELECT 1
            FROM teachers_to_students AS tts
            WHERE tts.student_id = students.id
        );

        SELECT teachers.id, teachers.first_name, teachers.last_name, ...
        FROM teachers
        WHERE teachers.id IN (:teacher_id_1, :teacher_id_2, ...);
    """
    stmt = (
        select(Student)
        .where(Student.teachers.any())
        .options(selectinload(Student.teachers))
        .order_by(Student.id)
    )
    students = session.execute(stmt).scalars().all()
    _print_with_relation(students, "teachers")


def get_students(session: Session) -> None:
    """Перші 5 студентів (LIMIT/OFFSET) з учителями через selectinload.

    SQL (~):
        SELECT students.*
        FROM students
        LIMIT 5 OFFSET 0;

        SELECT teachers.*
        FROM teachers
        WHERE teachers.id IN (:id_1, :id_2, ...);
    """
    stmt = (
        select(Student)
        .options(selectinload(Student.teachers))
        .order_by(Student.id)
        .limit(5)
        .offset(0)
    )
    students = session.execute(stmt).scalars().all()
    _print_with_relation(students, "teachers")


def get_teachers(session: Session) -> None:
    """Учителі, у яких є студенти (фільтр як inner join по колекції); студенти — selectinload.

    SQL (~):
        SELECT teachers.*
        FROM teachers
        WHERE EXISTS (
            SELECT 1
            FROM teachers_to_students AS tts
            WHERE tts.teacher_id = teachers.id
        );

        SELECT students.*
        FROM students
        WHERE students.id IN (:student_id_1, :student_id_2, ...);
    """
    stmt = (
        select(Teacher)
        .where(Teacher.students.any())
        .options(selectinload(Teacher.students))
        .order_by(Teacher.id)
    )
    teachers = session.execute(stmt).scalars().all()
    _print_with_relation(teachers, "students")


def get_teachers_outerjoin(session: Session) -> None:
    """Усі учителі; список студентів може бути порожнім (без фільтра students.any()).

    SQL (~):
        SELECT teachers.* FROM teachers;

        SELECT students.*
        FROM students
        WHERE students.id IN (:id_1, :id_2, ...);
    """
    stmt = select(Teacher).options(selectinload(Teacher.students)).order_by(Teacher.id)
    teachers = session.execute(stmt).scalars().all()
    _print_with_relation(teachers, "students")


def get_teachers_by_data(session: Session) -> None:
    """Учителі зі студентами та додатковим фільтром по start_work.

    Умова OR навмисно з «діркою»: start_work <= 2020-01-01 АБО >= 2021-12-31
    (між цими датами виключено, наприклад учитель з 2020-06-01 не потрапить).

    SQL (~):
        SELECT teachers.*
        FROM teachers
        WHERE EXISTS (
            SELECT 1
            FROM teachers_to_students AS tts
            WHERE tts.teacher_id = teachers.id
        )
        AND (
            teachers.start_work <= DATE '2020-01-01'
            OR teachers.start_work >= DATE '2021-12-31'
        );

        SELECT students.*
        FROM students
        WHERE students.id IN (:student_id_1, ...);
    """
    stmt = (
        select(Teacher)
        .where(
            Teacher.students.any(),
            or_(
                Teacher.start_work <= date(2020, 1, 1),
                Teacher.start_work >= date(2021, 12, 31),
            ),
        )
        .options(selectinload(Teacher.students))
        .order_by(Teacher.id)
    )
    teachers = session.execute(stmt).scalars().all()
    _print_with_relation(teachers, "students", extra_attrs=("start_work",))


def get_students_with_contacts(session: Session) -> None:
    """Студенти, у яких є контакти; контакти підвантажує selectinload.

    SQL (~):
        SELECT students.*
        FROM students
        WHERE EXISTS (
            SELECT 1
            FROM contacts AS c
            WHERE c.student_id = students.id
        );

        SELECT contacts.*
        FROM contacts
        WHERE contacts.student_id IN (:sid_1, :sid_2, ...);
    """
    stmt = (
        select(Student)
        .where(Student.contacts.any())
        .options(selectinload(Student.contacts))
        .order_by(Student.id)
    )
    students = session.execute(stmt).scalars().all()
    _print_with_relation(students, "contacts")


def get_info(session: Session) -> None:
    """Плоский SELECT: колонки студента, учителя й контакту; результат друкується як dict.

    Один і той самий student.id може повторитись багато разів: кожен рядок — пара
    (учитель з tts) × (контакт цього студента), тобто декартів добуток зв’язків.
    У студента 2 учителі й 2 контакти → до 4 рядків з його id.

    SQL (~):
        SELECT
            students.id AS id,
            (students.first_name || ' ' || students.last_name) AS fullname,
            (teachers.first_name || ' ' || teachers.last_name) AS teacher_fullname,
            (contacts.first_name || ' ' || contacts.last_name) AS contact_fullname
        FROM students
        JOIN teachers_to_students AS tts
            ON tts.student_id = students.id
        JOIN teachers
            ON teachers.id = tts.teacher_id
        JOIN contacts
            ON contacts.student_id = students.id
        ORDER BY students.id, teachers.id, contacts.id;
    """
    stmt = (
        select(
            Student.id,
            Student.fullname,
            Teacher.fullname.label("teacher_fullname"),
            Contact.fullname.label("contact_fullname"),
        )
        .select_from(Student)
        .join(TeacherStudent)
        .join(Teacher)
        .join(Contact)
        .order_by(Student.id, Teacher.id, Contact.id)
    )
    for row in session.execute(stmt).mappings():
        print(dict(row))


def update_student(
    session: Session, s_id: int, teachers: list[Teacher]
) -> Student | None:
    """Переписує many-to-many учителів студента і робить commit. Повертає None, якщо студента нема.

    SQL (~):
        SELECT students.*
        FROM students
        WHERE students.id = :s_id;

        DELETE FROM teachers_to_students
        WHERE teachers_to_students.student_id = :s_id;

        INSERT INTO teachers_to_students (teacher_id, student_id)
        VALUES
            (:teacher_id_1, :s_id),
            (:teacher_id_2, :s_id),
            ...;

        COMMIT;
    """
    student = session.get(Student, s_id)
    if student is None:
        return None
    student.teachers = teachers
    session.commit()
    return student


def remove_student(session: Session, s_id: int) -> int:
    """Видаляє студента за id (core delete) і commit; каскади — згідно з FK у БД.
    Повертає кількість видалених рядків students (0 або 1).

    SQL (~):
        -- Якщо ON DELETE CASCADE на contacts.student_id та tts.student_id,
        -- часто достатньо одного кроку:
        DELETE FROM students WHERE students.id = :s_id;

        -- Якщо CASCADE немає, типовий порядок:
        -- DELETE FROM contacts WHERE student_id = :s_id;
        -- DELETE FROM teachers_to_students WHERE student_id = :s_id;
        -- DELETE FROM students WHERE id = :s_id;

        COMMIT;
    """
    result = session.execute(delete(Student).where(Student.id == s_id))
    session.commit()
    return result.rowcount or 0


def _demo_update_student(session: Session) -> None:
    """Завантажує учителів з id 1, 2, 3 і викликає update_student для студента 8 (повний сценарій у БД).

    SQL (~):
        SELECT teachers.*
        FROM teachers
        WHERE teachers.id IN (1, 2, 3);

        SELECT students.*
        FROM students
        WHERE students.id = 8;

        DELETE FROM teachers_to_students
        WHERE teachers_to_students.student_id = 8;

        INSERT INTO teachers_to_students (teacher_id, student_id)
        VALUES
            (1, 8),
            (2, 8),
            (3, 8);

        COMMIT;
    """
    teachers = (
        session.execute(select(Teacher).where(Teacher.id.in_([1, 2, 3])))
        .scalars()
        .all()
    )
    st = update_student(session, 8, teachers)
    if st is None:
        print("Студента з id=8 не знайдено")
    else:
        session.refresh(st)
        print(
            {
                "id": st.id,
                "fullname": st.fullname,
                "teachers": [(t.id, t.fullname) for t in st.teachers],
            }
        )


def _demo_remove_student(session: Session) -> None:
    """Демонстрація видалення студента з id = 7 (те саме, що remove_student).

    SQL (~):
        DELETE FROM students WHERE students.id = 7;
        COMMIT;
        -- залежні рядки (contacts, teachers_to_students) зникають через ON DELETE CASCADE, якщо так задано в схемі.
    """
    n = remove_student(session, 7)
    if n:
        print(f"Видалено студента id=7 (DELETE повернув {n} рядок(ів) у students).")
    else:
        print("Студента з id=7 не знайдено — нічого не видалено.")


EXAMPLES: list[tuple[str, Callable[[Session], None]]] = [
    ("Студенти з учителями (лише ті, хто має зв’язок)", get_student_join),
    ("П’ять студентів з учителями", get_students),
    ("Учителі, у яких є студенти", get_teachers),
    ("Усі учителі зі списком студентів", get_teachers_outerjoin),
    ("Учителі з фільтром по даті початку роботи", get_teachers_by_data),
    ("Студенти, у яких є контакти", get_students_with_contacts),
    (
        "Плоскі колонки: студент × учитель × контакт (дублі id — декартів добуток)",
        get_info,
    ),
    ("Оновити студента 8: учителі 1, 2, 3", _demo_update_student),
    ("Видалити студента 7", _demo_remove_student),
]


if __name__ == "__main__":
    for i, (title, _) in enumerate(EXAMPLES, start=1):
        print(f"  {i}. {title}")
    print("  0. вихід")

    with SessionLocal() as session:
        while True:
            raw = input("Номер прикладу: ").strip()
            if raw == "0":
                break
            try:
                n = int(raw)
            except ValueError:
                print("Потрібне число.")
                continue
            if not 1 <= n <= len(EXAMPLES):
                print("Невідомий номер.")
                continue
            title, run_fn = EXAMPLES[n - 1]
            print(f"\n[{n}] {title}\nЩо отримуємо:\n")
            run_fn(session)
            print()
