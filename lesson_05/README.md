# Заняття 5 — SQLAlchemy: Core, ORM, сесії, async, завантаження зв’язків

Навчальні скрипти демонструють роботу з БД через **SQLAlchemy 2.x** (SQLite). Запускайте файли з кореня каталогу `lesson_05` або вкажіть шлях до них.

## Залежності

З кореня `lesson_05` (там же лежить `pyproject.toml`):

```powershell
uv sync
```

Пакети вже прописані в проєкті: `sqlalchemy`, `aiosqlite`.

## Порядок і зміст файлів

| Файл                                | Тема                                                                                 |
| ----------------------------------- | ------------------------------------------------------------------------------------ |
| `01_orm_core_01.py`                 | Core: таблиці, INSERT / SELECT / UPDATE / DELETE, JOIN                               |
| `02_orm_core_02.py`                 | Core: `WHERE`, `AND` / `OR` / `NOT`, агрегати, `GROUP BY`, `ORDER BY`                |
| `03_orm_core_03.py`                 | Core: транзакції (`engine.begin()`), приклад переказу між рахунками                  |
| `04_orm_core_04.py`                 | Виконання сирих запитів через `text()`, параметри                                    |
| `05_orm_relationship.py`            | ORM: моделі, зв’язки 1:N, N:M, 1:1; сид і демо-запити (`school.db`)                  |
| `06_orm_session.py`                 | Сесія, `session_scope`, CRUD з **явною передачею `session`** (`session_example.db`)  |
| `07_orm_async.py`                   | Асинхронний двигун і сесія, CRUD, `selectinload` (in-memory SQLite)                  |
| `08_orm_execute.py`                 | ORM + `select` / JOIN / підзапити / CTE / `update` / `text` (`modern_sqlalchemy.db`) |
| `09_lazy_loading.py`                | Lazy loading і проблема N+1 (`lazy_loading.db`, `echo=True`)                         |
| `10_eager_loading.py`               | Порівняння `joinedload`, `subqueryload`, `selectinload` (`eager_loading.db`)         |
| `11_async_eager_loading_example.py` | Async + eager loading (`async_eager.db`)                                             |

## Шпаргалка: `joinedload` / `subqueryload` / `selectinload`

Мета eager loading: **уникнути N+1**. Тобто: щоб при обході `author.books` / `book.genres` ORM **не виконував** окремий SQL-запит для кожного пов’язаного об’єкта.

### Вибір стратегії (практичне правило за замовчуванням)

- **Колекції (1:N, N:M як колекція)**: типовий перший вибір — **`selectinload()`**.
- **Одиничні зв’язки (N:1, 1:1)**: зазвичай доречно — **`joinedload()`**.
- **`subqueryload()`**: зазвичай використовується рідше; типовий сценарій — або історична причина, або специфічний SQL-план. Якщо немає причини обирати `subqueryload`, типовим вибором є `selectinload`.

### Що робить кожен метод на рівні SQL

- **`joinedload()`**: додає `JOIN` в основний SELECT (часто 1 великий SQL).  
  - **Плюс**: 1 запит.  
  - **Мінус**: якщо джойнити *колекції* (1:N), результат “роздувається” (один `Author` повторюється стільки разів, скільки в нього `Book`, і т.д.). Це може стати повільно; також при `session.execute(...)` для такого запиту зазвичай потрібне “згладжування” дублікатів через `result.unique()` (див. приклад у `10_eager_loading.py`).

- **`selectinload()`**: робить 1 запит на батьків, потім ще 1 (або кілька) запитів на дітей через `WHERE ... IN (...)`.  
  - **Плюс**: не роздуває рядки JOIN-ами; добре масштабується на колекціях.  
  - **Мінус**: 2+ запити (але контрольовано, не N+1).

- **`subqueryload()`**: теж 2+ запити, але дочірні дані тягне через підзапит (`FROM (subquery) ...`).  
  - **Плюс/мінус**: залежить від СУБД/форми запиту; для першого знайомства достатньо знати, що це “альтернатива `selectinload`”.

### Практичний рецепт для цього уроку (див. `10_eager_loading.py`)

1) Колекції завантажуємо через **`selectinload`**  
2) На “останньому кроці” до одиничного об’єкта зазвичай ставимо **`joinedload`**

Міні-приклад (Author 1:N Books, Book 1:N BookGenre, BookGenre N:1 Genre):

```python
stmt = select(Author).options(
    selectinload(Author.books).selectinload(Book.genres).joinedload(BookGenre.genre)
)
```

Перевірка вибору:
- якщо атрибут зв’язку — **колекція** (`Mapped[list[...]]`), типовий вибір — `selectinload`
- якщо атрибут зв’язку — **один об’єкт** (`Mapped[Genre]`, `Mapped[Department]`), зазвичай доречний — `joinedload`

## Запуск

```powershell
uv run python 01_orm_core_01.py
# … або будь-який інший файл з таблиці вище
```
