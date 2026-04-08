# lazy_loading_example.py

from sqlalchemy import create_engine, String, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, relationship, Session, Mapped, mapped_column
import time

# Створення двигуна
engine = create_engine("sqlite:///lazy_loading.db", echo=True)


# Базовий клас моделі
class Base(DeclarativeBase):
    pass


# Визначення моделей
class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    # Зв'язок один-до-багатьох з книгами
    books: Mapped[list["Book"]] = relationship(back_populates="author")

    def __repr__(self):
        return f"Author(id={self.id}, name='{self.name}')"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))

    # Зв'язок багато-до-одного з автором
    author: Mapped["Author"] = relationship(back_populates="books")

    # Зв'язок один-до-багатьох з жанрами
    genres: Mapped[list["BookGenre"]] = relationship(back_populates="book")

    def __repr__(self):
        return f"Book(id={self.id}, title='{self.title}')"


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    # Зв'язок один-до-багатьох з книгами через асоціативну таблицю
    books: Mapped[list["BookGenre"]] = relationship(back_populates="genre")

    def __repr__(self):
        return f"Genre(id={self.id}, name='{self.name}')"


class BookGenre(Base):
    __tablename__ = "book_genres"

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), primary_key=True)

    # Зв'язки з книгою та жанром
    book: Mapped["Book"] = relationship(back_populates="genres")
    genre: Mapped["Genre"] = relationship(back_populates="books")

    def __repr__(self):
        return f"BookGenre(book_id={self.book_id}, genre_id={self.genre_id})"


# Створення таблиць та заповнення тестовими даними
def setup_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Створення жанрів
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

        # Створення авторів та їхніх книг
        authors_data = [
            {
                "name": "Дж. К. Роулінг",
                "books": [
                    {
                        "title": "Гаррі Поттер і філософський камінь",
                        "genres": ["Fantasy"],
                    },
                    {"title": "Гаррі Поттер і таємна кімната", "genres": ["Fantasy"]},
                    {"title": "Гаррі Поттер і в'язень Азкабану", "genres": ["Fantasy"]},
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
                    {"title": "Вбивство у Східному експресі", "genres": ["Mystery"]},
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

        session.commit()

    print("База даних створена та заповнена тестовими даними")


def lazy_loading_demo():
    print("\n=== Демонстрація проблеми N+1 запитів з Lazy Loading ===")

    with Session(engine) as session:
        # Тимчасово вимикаємо виведення SQL для чистоти виводу
        # engine.echo = False

        print("\nОтримання всіх авторів (1 запит)")
        start_time = time.perf_counter()
        stmt = select(Author)
        authors = session.scalars(
            stmt
        ).all()  # scalars(stmt) == execute(stmt).scalars()

        # Лічильник запитів
        query_count = 1  # 1 вже виконано для отримання авторів

        print(f"\nВиведення інформації про авторів та їхні книги:")
        for author in authors:
            print(f"\nАвтор: {author.name}")

            # Lazy loading: це викличе додатковий запит для кожного автора
            books = author.books
            query_count += 1

            print(f"  Книги ({len(books)}):")
            for book in books:
                print(f"    - {book.title}")

                # Lazy loading: це викличе додатковий запит для кожної книги
                book_genres = book.genres
                query_count += 1

                genre_names = []
                for book_genre in book_genres:
                    # Lazy loading: це викличе додатковий запит для кожного book_genre
                    genre = book_genre.genre
                    query_count += 1
                    genre_names.append(genre.name)

                print(f"      Жанри: {', '.join(genre_names)}")

        end_time = time.perf_counter()
        execution_time = end_time - start_time

        print(f"\nЗагальна кількість запитів: {query_count}")
        print(f"Час виконання: {execution_time:.6f} секунд")

        # Повертаємо виведення SQL
        engine.echo = True


if __name__ == "__main__":
    setup_database()
    lazy_loading_demo()
