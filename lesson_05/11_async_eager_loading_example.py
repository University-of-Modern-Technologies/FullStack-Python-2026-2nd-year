# async_eager_loading_example.py

import asyncio
import time

from sqlalchemy import String, ForeignKey, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    Mapped,
    mapped_column,
    selectinload,
)

# створення асинхронного двигуна
engine = create_async_engine("sqlite+aiosqlite:///async_eager.db", echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# базовий клас моделі
class Base(DeclarativeBase):
    pass


# визначення моделей
class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    # зв’язок один-до-багатьох з книгами
    books: Mapped[list["Book"]] = relationship(back_populates="author")

    def __repr__(self):
        return f"Author(id={self.id}, name='{self.name}')"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))

    # зв’язок багато-до-одного з автором
    author: Mapped["Author"] = relationship(back_populates="books")

    # зв’язок один-до-багатьох з жанрами (через асоціативну таблицю book_genres)
    genres: Mapped[list["BookGenre"]] = relationship(back_populates="book")

    def __repr__(self):
        return f"Book(id={self.id}, title='{self.title}')"


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    # зв’язок один-до-багатьох з книгами через асоціативну таблицю
    books: Mapped[list["BookGenre"]] = relationship(back_populates="genre")

    def __repr__(self):
        return f"Genre(id={self.id}, name='{self.name}')"


class BookGenre(Base):
    __tablename__ = "book_genres"

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), primary_key=True)

    # зв’язки з книгою та жанром
    book: Mapped["Book"] = relationship(back_populates="genres")
    genre: Mapped["Genre"] = relationship(back_populates="books")

    def __repr__(self):
        return f"BookGenre(book_id={self.book_id}, genre_id={self.genre_id})"


# асинхронна функція для налаштування бази даних
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        async with session.begin():
            # створення жанрів
            genres = {
                "Fantasy": Genre(name="Fantasy"),
                "Sci-Fi": Genre(name="Science Fiction"),
                "Mystery": Genre(name="Mystery"),
                "Romance": Genre(name="Romance"),
                "Horror": Genre(name="Horror"),
                "History": Genre(name="History"),
            }

            for genre in genres.values():
                session.add(genre)

            # створення авторів та їхніх книг
            authors_data = [
                {
                    "name": "Дж. К. Роулінг",
                    "books": [
                        {
                            "title": "Гаррі Поттер і філософський камінь",
                            "genres": ["Fantasy"],
                        },
                        {
                            "title": "Гаррі Поттер і таємна кімната",
                            "genres": ["Fantasy"],
                        },
                        {
                            "title": "Гаррі Поттер і в'язень Азкабану",
                            "genres": ["Fantasy"],
                        },
                    ],
                },
                {
                    "name": "Джордж Р. Р. Мартін",
                    "books": [
                        {"title": "Гра престолів", "genres": ["Fantasy"]},
                        {"title": "Битва королів", "genres": ["Fantasy"]},
                        {"title": "Буря мечів", "genres": ["Fantasy"]},
                    ],
                },
                {
                    "name": "Агата Крісті",
                    "books": [
                        {"title": "Вбивство на полі для гольфу", "genres": ["Mystery"]},
                        {
                            "title": "Вбивство у Східному експресі",
                            "genres": ["Mystery"],
                        },
                        {"title": "І нікого не стало", "genres": ["Mystery", "Horror"]},
                    ],
                },
                {
                    "name": "Айзек Азімов",
                    "books": [
                        {"title": "Фундація", "genres": ["Sci-Fi"]},
                        {"title": "Я, робот", "genres": ["Sci-Fi"]},
                        {"title": "Кінець вічності", "genres": ["Sci-Fi", "Romance"]},
                    ],
                },
                {
                    "name": "Стівен Кінг",
                    "books": [
                        {"title": "Сяйво", "genres": ["Horror"]},
                        {"title": "Воно", "genres": ["Horror"]},
                        {"title": "11/22/63", "genres": ["Sci-Fi", "History"]},
                    ],
                },
            ]

            for author_data in authors_data:
                author = Author(name=author_data["name"])
                session.add(author)

                for book_data in author_data["books"]:
                    book = Book(title=book_data["title"], author=author)
                    session.add(book)

                    for genre_name in book_data["genres"]:
                        book_genre = BookGenre(book=book, genre=genres[genre_name])
                        session.add(book_genre)

    print("База даних створена та заповнена тестовими даними")


# асинхронна демонстрація eager loading
async def eager_loading_demo():
    print(
        "\n=== Демонстрація жадного завантаження (selectinload) в асинхронному режимі ==="
    )

    async with async_session() as session:
        # вимикаємо виведення SQL, щоби було легше спостерігати загальну кількість запитів
        engine.echo = True

        start_time = time.perf_counter()

        # виконуємо запит з явним використанням eager loading для книг і жанрів
        # тут selectinload(Author.books) підтягне усі книги,
        # а наступний selectinload(Book.genres).selectinload(BookGenre.genre)
        # підтягне BookGenre і пов’язані жанри
        stmt = select(Author).options(
            selectinload(Author.books)
            .selectinload(Book.genres)
            .selectinload(BookGenre.genre)
        )
        result = await session.execute(stmt)
        authors = result.scalars().all()

        # тут буде один великий або декілька великих запитів,
        # але не “пачка” дрібних, як було б у випадку lazy loading

        print(
            f"\nОтримали авторів зі всіма потрібними пов'язаними даними (книги та жанри)."
        )
        for author in authors:
            print(f"\nАвтор: {author.name}")
            books = author.books  # вже завантажені, не виконується додатковий запит
            print(f"  Книги ({len(books)}):")
            for book in books:
                print(f"    — {book.title}")

                # genres — це список BookGenre, які також уже завантажені
                book_genres = book.genres
                genre_names = [
                    bg.genre.name for bg in book_genres
                ]  # bg.genre теж готовий
                print(f"      Жанри: {', '.join(genre_names)}")

        end_time = time.perf_counter()
        execution_time = end_time - start_time

        print(f"Час виконання: {execution_time:.6f} секунд")

        # повертаємо виведення SQL
        engine.echo = True


# головна асинхронна функція
async def main():
    await setup_database()
    await eager_loading_demo()


# запуск асинхронної програми
if __name__ == "__main__":
    asyncio.run(main())
