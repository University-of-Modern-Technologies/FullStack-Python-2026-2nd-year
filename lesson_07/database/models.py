from sqlalchemy import ForeignKey, String, Boolean, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from database.db import engine


class Base(DeclarativeBase):
    pass


class Owner(Base):
    __tablename__ = "owners"
    id: Mapped[int] = mapped_column(primary_key=True)
    fullname = mapped_column(String(50))
    email = mapped_column(String(50))
    cats = relationship("Cat", back_populates="owner")


class Cat(Base):
    __tablename__ = "cats"
    id: Mapped[int] = mapped_column(primary_key=True)
    nick = mapped_column(String(50))
    age = mapped_column(Integer)
    vaccinated = mapped_column(Boolean)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"))
    owner = relationship("Owner", back_populates="cats")


Base.metadata.create_all(engine)
