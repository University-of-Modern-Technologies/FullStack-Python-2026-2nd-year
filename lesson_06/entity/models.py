from datetime import date

from sqlalchemy import Date, ForeignKey, String, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Teacher(Base):
    __tablename__ = "teachers"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column("cell_phone", String(100))
    address: Mapped[str | None] = mapped_column(String(100))
    start_work: Mapped[date] = mapped_column(Date, nullable=False)
    students: Mapped[list[Student]] = relationship(
        secondary="teachers_to_students",
        back_populates="teachers",
    )

    @hybrid_property  # for order_by, select
    def fullname(self) -> str:
        return self.first_name + " " + self.last_name

    @fullname.expression  # for filter, filter_by
    def fullname(cls):
        return func.concat(cls.first_name, " ", cls.last_name)


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column("cell_phone", String(100))
    address: Mapped[str | None] = mapped_column(String(100))
    teachers: Mapped[list[Teacher]] = relationship(
        secondary="teachers_to_students",
        back_populates="students",
    )
    contacts: Mapped[list[Contact]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )

    @hybrid_property
    def fullname(self) -> str:
        return self.first_name + " " + self.last_name


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column("cell_phone", String(100))
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    student: Mapped[Student] = relationship(back_populates="contacts")

    @hybrid_property
    def fullname(self) -> str:
        return self.first_name + " " + self.last_name


class TeacherStudent(Base):
    __tablename__ = "teachers_to_students"
    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
