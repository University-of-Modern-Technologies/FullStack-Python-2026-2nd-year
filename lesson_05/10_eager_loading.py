# eager_loading_example.py

from sqlalchemy import create_engine, String, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, relationship, Session, Mapped, mapped_column
from sqlalchemy.orm import joinedload, subqueryload, selectinload
import time

# Створення двигуна
engine = create_engine("sqlite:///eager_loading.db", echo=False)  # echo=False для чистоти виводу


# Базовий клас моделі
class Base(DeclarativeBase):
    pass


# Визначення моделей
class Author(Base):
    __tablename__ = 'authors'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    books: Mapped[list["Book"]] = relationship(back_populates="author")

    def __repr__(self):
        return f"Author(id={self.id}, name='{self.name}')"


class Book(Base):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(ForeignKey('authors.id'))

    author: Mapped["Author"] = relationship(back_populates="books")
    genres: Mapped[list["BookGenre"]] = relationship(back_populates="book")

    def __repr__(self):
        return f"Book(id={self.id}, title='{self.title}')"


class Genre(Base):
    __tablename__ = 'genres'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    books: Mapped[list["BookGenre"]] = relationship(back_populates="genre")

    def __repr__(self):
        return f"Genre(id={self.id}, name='{self.name}')"


class BookGenre(Base):
    __tablename__ = 'book_genres'

    book_id: Mapped[int] = mapped_column(ForeignKey('books.id'), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey('genres.id'), primary_key=True)

    book: Mapped["Book"] = relationship(back_populates="genres")
    genre: Mapped["Genre"] = relationship(back_populates="books")

    def __repr__(self):
        return f"BookGenre(book_id={self.book_id}, genre_id={self.genre_id})"


# Функція налаштування бази даних
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
                    {"title": "Гаррі Поттер і філософський камінь", "genres": ["Fantasy"]},
                    {"title": "Гаррі Поттер і таємна кімната", "genres": ["Fantasy"]},
                    {"title": "Гаррі Поттер і в'язень Азкабану", "genres": ["Fantasy"]},
                ]
            },
            {
                "name": "Джордж Р. Р. Мартін",
                "books": [
                    {"title": "Гра престолів", "genres": ["Fantasy"]},
                    {"title": "Битва королів", "genres": ["Fantasy"]},
                    {"title": "Буря мечів", "genres": ["Fantasy"]},
                ]
            },
            {
                "name": "Агата Крісті",
                "books": [
                    {"title": "Вбивство на полі для гольфу", "genres": ["Mystery"]},
                    {"title": "Вбивство у Східному експресі", "genres": ["Mystery"]},
                    {"title": "І нікого не стало", "genres": ["Mystery", "Horror"]},
                ]
            },
            {
                "name": "Айзек Азімов",
                "books": [
                    {"title": "Фундація", "genres": ["Sci-Fi"]},
                    {"title": "Я, робот", "genres": ["Sci-Fi"]},
                    {"title": "Кінець вічності", "genres": ["Sci-Fi", "Romance"]},
                ]
            },
            {
                "name": "Стівен Кінг",
                "books": [
                    {"title": "Сяйво", "genres": ["Horror"]},
                    {"title": "Воно", "genres": ["Horror"]},
                    {"title": "11/22/63", "genres": ["Sci-Fi", "History"]},
                ]
            }
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


# Функція для виведення інформації
def print_author_info(authors):
    for author in authors:
        print(f"\nАвтор: {author.name}")
        print(f"  Книги ({len(author.books)}):")
        for book in author.books:
            print(f"    - {book.title}")

            genre_names = []
            for book_genre in book.genres:
                genre_names.append(book_genre.genre.name)

            print(f"      Жанри: {', '.join(genre_names)}")


# Демонстрація різних стратегій eager loading
def compare_loading_strategies():
    print("\n=== Порівняння різних стратегій завантаження ===")

    # Тимчасово вмикаємо виведення SQL для аналізу запитів
    engine.echo = True

    with Session(engine) as session:
        # 1. Lazy loading (за замовчуванням)
        print("\n1. Lazy Loading (за замовчуванням)")
        print("--------------------------------------")
        start_time = time.perf_counter()

        stmt = select(Author)
        authors = session.scalars(stmt).all()
        # Доступ до зв'язаних об'єктів (викличе додаткові запити)
        for author in authors:
            for book in author.books:
                for book_genre in book.genres:
                    _ = book_genre.genre.name

        end_time = time.perf_counter()
        lazy_time = end_time - start_time
        print(f"Час виконання: {lazy_time:.6f} секунд")

    with Session(engine) as session:
        # 2. Eager loading з joinedload
        print("\n2. Eager Loading з joinedload()")
        print("--------------------------------------")
        start_time = time.perf_counter()

        # Завантаження авторів разом з книгами та жанрами
        stmt = select(Author).options(
            joinedload(Author.books).joinedload(Book.genres).joinedload(BookGenre.genre)
        )
        result = session.execute(stmt)  # Виконуємо запит
        result = result.unique()  # "Згладжуємо" дублікати
        authors = result.scalars().all()  # Отримуємо ORM-об'єкти

        # Всі дані вже завантажені, запитів не буде
        for author in authors:
            for book in author.books:
                for book_genre in book.genres:
                    _ = book_genre.genre.name

        end_time = time.perf_counter()
        joined_time = end_time - start_time
        print(f"Час виконання: {joined_time:.6f} секунд")

    with Session(engine) as session:
        # 3. Eager loading з subqueryload
        print("\n3. Eager Loading з subqueryload()")
        print("--------------------------------------")
        start_time = time.perf_counter()

        # Завантаження авторів разом з книгами та жанрами
        stmt = select(Author).options(
            subqueryload(Author.books).subqueryload(Book.genres).subqueryload(BookGenre.genre)
        )
        authors = session.scalars(stmt).all()

        # Всі дані вже завантажені, запитів не буде
        for author in authors:
            for book in author.books:
                for book_genre in book.genres:
                    _ = book_genre.genre.name

        end_time = time.perf_counter()
        subquery_time = end_time - start_time
        print(f"Час виконання: {subquery_time:.6f} секунд")

    with Session(engine) as session:
        # 4. Eager loading з selectinload
        print("\n4. Eager Loading з selectinload()")
        print("--------------------------------------")
        start_time = time.perf_counter()

        # Завантаження авторів разом з книгами та жанрами
        stmt = select(Author).options(
            selectinload(Author.books).selectinload(Book.genres).selectinload(BookGenre.genre)
        )
        authors = session.scalars(stmt).all()

        # Всі дані вже завантажені, запитів не буде
        for author in authors:
            for book in author.books:
                for book_genre in book.genres:
                    _ = book_genre.genre.name

        end_time = time.perf_counter()
        selectin_time = end_time - start_time
        print(f"Час виконання: {selectin_time:.6f} секунд")

    # Вимикаємо виведення SQL для наступного виведення
    engine.echo = False

    print("\n=== Демонстрація результатів ===")

    with Session(engine) as session:
        print("\n5. Комбінована стратегія (рекомендовано)")
        print("--------------------------------------")
        start_time = time.perf_counter()

        # Використання різних стратегій для різних зв'язків:
        # - joinedload для багато-до-одного (BookGenre -> Genre)
        # - selectinload для один-до-багатьох (Author -> Books -> BookGenres)
        stmt = select(Author).options(
            selectinload(Author.books).selectinload(Book.genres).joinedload(BookGenre.genre)
        )
        authors = session.scalars(stmt).all()

        print_author_info(authors)

        end_time = time.perf_counter()
        combined_time = end_time - start_time
        print(f"Час виконання: {combined_time:.6f} секунд")

    print("\n=== Підсумки порівняння ===")
    print(f"Lazy loading:     {lazy_time:.6f} секунд")
    print(f"joinedload():     {joined_time:.6f} секунд")
    print(f"subqueryload():   {subquery_time:.6f} секунд")
    print(f"selectinload():   {selectin_time:.6f} секунд")
    print(f"Комбінована:      {combined_time:.6f} секунд")

    print("\nВідносна ефективність:")
    if lazy_time > 0:
        print(f"  joinedload vs lazy:    {lazy_time / joined_time:.2f}x швидше")
        print(f"  subqueryload vs lazy:  {lazy_time / subquery_time:.2f}x швидше")
        print(f"  selectinload vs lazy:  {lazy_time / selectin_time:.2f}x швидше")
        print(f"  Комбінована vs lazy:   {lazy_time / combined_time:.2f}x швидше")


if __name__ == "__main__":
    setup_database()
    compare_loading_strategies()