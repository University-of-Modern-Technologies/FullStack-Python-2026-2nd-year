# Lesson 08: Todo API

Навчальний FastAPI-проєкт з асинхронним доступом до PostgreSQL через SQLAlchemy та міграціями Alembic.

## Вимоги

- Python 3.14+
- PostgreSQL
- uv

## Налаштування

Скопіюй приклад змінних оточення:

```bash
cp .env.example .env
```

Онови значення в `.env` під свою локальну базу даних.

## Встановлення залежностей

```bash
uv sync
```

## Міграції

Застосувати вже створені міграції:

```bash
uv run alembic upgrade head
```

### Створення міграцій з нуля

Ініціалізувати Alembic для async-проєкту:

```bash
uv run alembic init -t async migrations
```

Після цього в проєкті з'являться директорія `migrations` та файл `alembic.ini`.

У `alembic.ini` параметр `sqlalchemy.url` можна залишити як placeholder, якщо реальний URL підставляється в `migrations/env.py` з налаштувань проєкту:

```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

Для PostgreSQL з asyncpg рядок підключення має такий формат:

```text
postgresql+asyncpg://user:password@localhost:5432/todo_app
```

У `migrations/env.py` потрібно підключити метадані моделей, щоб Alembic бачив таблиці під час автогенерації:

```python
from src.conf.config import settings
from src.entity.models import Base

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", settings.DB_URL)
```

Створити першу міграцію на основі моделей:

```bash
uv run alembic revision --autogenerate -m "Initial migration"
```

Застосувати міграцію до бази:

```bash
uv run alembic upgrade head
```

## Запуск

```bash
uv run fastapi dev main.py
```

API буде доступне за адресою:

```text
http://127.0.0.1:8000
```

Документація Swagger:

```text
http://127.0.0.1:8000/docs
```
