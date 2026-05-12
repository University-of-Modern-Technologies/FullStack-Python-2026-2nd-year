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

## Авторизація

У проєкті є access JWT + refresh token:

- `POST /api/auth/register` - реєстрація користувача
- `POST /api/auth/login` - логін, повертає `access_token` і `refresh_token`
- `POST /api/auth/refresh` - приймає refresh token, повертає новий access token
- `POST /api/auth/logout` - видаляє refresh token з БД
- `GET /api/auth/me` - поточний користувач з access JWT

`access_token` - це JWT. `refresh_token` - opaque random token; у БД зберігається тільки його SHA-256 hash.

Усі `/api/todos/*` маршрути потребують `Authorization: Bearer <access_token>`. Кожен todo прив'язаний до користувача, тому користувач бачить і змінює тільки свої записи.

### Приклад Flow

Реєстрація:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","email":"bob@example.com","password":"secret123"}'
```

Логін:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=bob&password=secret123"
```

Створення todo:

```bash
curl -X POST http://127.0.0.1:8000/api/todos/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn JWT","description":"Access + refresh tokens"}'
```

Refresh access token:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```
