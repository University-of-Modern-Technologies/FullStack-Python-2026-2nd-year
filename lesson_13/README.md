# Lesson 13: Документація і тести для захищеного Todo API

Навчальний FastAPI-проєкт із реєстрацією, JWT/refresh-токенами, підтвердженням email, RBAC-ролями, CORS, rate limiting, IP blacklist, Redis-кешем списків todo, Cloudinary avatar upload, Sphinx-документацією та pytest-тестами.

## Вимоги

- Python 3.14+
- uv
- Docker (Postgres + Redis)
- SMTP-акаунт для відправки листів
- Cloudinary-акаунт для avatar upload

## Швидкий старт

```bash
cp .env.example .env
uv sync
docker compose up -d
uv run alembic upgrade head
uv run python scripts/seed_users.py
uv run fastapi dev main.py
```

- API: <http://127.0.0.1:8000>
- Swagger: <http://127.0.0.1:8000/docs>
- Sphinx HTML: `docs/_build/html/index.html` після збірки документації

**Seed-користувачі** (`scripts/seed_users.py`): `user_demo`, `mod_demo`, `admin_demo` — пароль `demo1234`.

## Конфігурація `.env`

Перед запуском потрібно заповнити значення для пошти та Cloudinary:

```env
EMAIL_TOKEN_SECRET_KEY=change-me-email-token-secret-32b
EMAIL_VERIFY_EXPIRE_HOURS=24
APP_PUBLIC_URL=http://127.0.0.1:8000

MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_FROM_NAME=Todo API
MAIL_SERVER=smtp.meta.ua
MAIL_PORT=465
MAIL_STARTTLS=False
MAIL_SSL_TLS=True

CLD_NAME=
CLD_API_KEY=
CLD_API_SECRET=
```

`APP_PUBLIC_URL` має бути доступним з листа. Для локальної розробки достатньо `http://127.0.0.1:8000`; для демонстрації через тунель потрібно вказати публічний URL.

## Архітектура

```text
HTTP -> middleware (IP, CORS) -> routes -> services -> repository -> Postgres
                                             |          |
                                             |          -> Redis cache
                                             -> email / Cloudinary
```

| Шар | Папка | Роль |
| ----- | ------- | ------ |
| Routes | `src/routes/` | HTTP, `Depends`, `response_model`, background tasks |
| Services | `src/services/` | Бізнес-логіка: auth, users, todos, email, avatars |
| Repository | `src/repository/` | SQL / ORM |
| Templates | `src/templates/` | HTML-шаблони листів і сторінки результату verify |
| Middleware | `src/middleware/` | IP blacklist, CORS у `main.py` |
| Schemas | `src/schemas/` | Pydantic: `user.py`, `auth.py`, `todo.py` |

### Документація

Документація живе в `docs/` і збирається Sphinx з Python docstring-ів через `sphinx.ext.autodoc`, `autosummary`, `napoleon` і `viewcode`.

```bash
uv run sphinx-build -b html docs docs/_build/html
```

На Windows також можна запускати:

```powershell
cd docs
.\make.bat html
```

Головний файл документації: [docs/index.rst](docs/index.rst). Зібрана HTML-версія відкривається з `docs/_build/html/index.html`.

Sphinx-довідник описує:

- точку входу `main.py`;
- конфігурацію `src/conf/`;
- базу даних, ORM-моделі та Alembic-міграції;
- middleware, limiter, repositories, services, routes і schemas;
- допоміжні скрипти `scripts/seed_users.py` та `scripts/smoke_test.py`.

Окремий markdown-файл для IP blacklist: [src/middleware/ip_block.md](src/middleware/ip_block.md).

## Тема 13 — огляд

| Тема | Код | Перевірка |
| ------ | ----- | ----------- |
| Email verification token | `src/services/auth.py` | register -> лист -> `/api/auth/verify-email?token=...` |
| SMTP-відправка | `src/services/email.py`, `src/templates/email/verify_email.html` | після register приходить HTML-лист |
| Сторінка результату verify | `src/templates/pages/verify_email_result.html` | відкриття verify link у браузері |
| Заборона login без verify | `src/services/auth.py` | непідтверджений user отримує `403` |
| Повторна відправка verify | `POST /api/auth/resend-verification` | непідтверджений email отримує новий лист |
| Cloudinary avatar upload | `src/services/avatars.py`, `PATCH /api/users/me/avatar` | upload image -> `avatar_url` у відповіді |
| Міграції БД | `d7fcd0fb3a59_add_email_confirmed.py`, `3ad4c05a1470_add_avatar.py` | `users.email_verified`, `users.avatar_url` |
| Sphinx-документація | `docs/` | HTML-довідник з autodoc |
| Pytest-тести | `tests/` | route, auth, RBAC, todo CRUD, avatar scenarios |

## Тести

Тестовий набір лежить у `tests/` і використовує `pytest`, `pytest-asyncio`, `pytest-cov`, `TestClient` та in-memory SQLite через `aiosqlite`. Зовнішні сервіси в тестах замокані: Redis cache, email-відправка і Cloudinary upload не потребують реальних облікових даних.

Запуск усіх тестів:

```bash
uv run pytest
```

Запуск із coverage:

```bash
uv run pytest --cov=src --cov=main --cov=scripts --cov-report=term-missing --cov-report=html
```

HTML-звіт coverage після запуску доступний у `htmlcov/index.html`.

Поточні групи тестів:

- `tests/test_auth_routes.py` — register, duplicate register, login, email verification, resend verification, refresh token;
- `tests/test_api_routes.py` — root, health, readiness, `/me`, avatar route, todo CRUD, ізоляція todo між користувачами, RBAC;
- `tests/test_avatars.py` — сервіс завантаження avatar і помилка Cloudinary;
- `tests/conftest.py` — тестова БД, seed-користувачі, JWT headers і mocks.

Примітка: тест logout revocation зараз позначений `skip`, бо поведінка відкликання refresh-токена ще переглядається.

## API

### Auth (`src/routes/auth.py`)

| Метод | Шлях | Примітка |
| ------- | ------ | ---------- |
| POST | `/api/auth/register` | створює user і фоново відправляє verification email |
| GET | `/api/auth/verify-email?token=...` | підтверджує email, повертає HTML-сторінку |
| POST | `/api/auth/resend-verification` | body: `email`; завжди `204`, щоб не розкривати наявність email |
| POST | `/api/auth/login` | form OAuth2; працює лише після підтвердження email |
| POST | `/api/auth/refresh` | body: `refresh_token` |
| POST | `/api/auth/logout` | Bearer + `refresh_token` |

### Users (`src/routes/users.py`)

| Метод | Шлях | Примітка |
| ------- | ------ | ---------- |
| GET | `/api/users/me` | Bearer, rate limit |
| PATCH | `/api/users/me/avatar` | Bearer, `multipart/form-data`, поле `file`, лише `image/*`, до 5MB |

### Todos (`src/routes/todos.py`)

`GET/POST/PUT/PATCH/DELETE /api/todos/*` — Bearer, лише власні todos.

### RBAC demo (`src/routes/access.py`)

Префікс `/api/access`:

| Метод | Шлях | Хто |
| ------- | ------ | ----- |
| GET | `/user` | будь-який з токеном |
| GET | `/moderator/todos` | moderator, admin |
| GET | `/admin/users` | admin |
| PATCH | `/admin/users/{id}/role` | admin |

### Health

- `GET /healthz` — процес живий
- `GET /readyz` — Postgres + Redis

## Лабораторні сценарії

### 1. Реєстрація з підтвердженням email

1. Заповни SMTP-змінні в `.env`.
2. `POST /api/auth/register`.
3. Відкрий link з листа.
4. `POST /api/auth/login` -> `200`.

До підтвердження email login повертає `403`.

### 2. Повторна відправка листа

```http
POST /api/auth/resend-verification
Content-Type: application/json

{
  "email": "student@example.com"
}
```

Endpoint повертає `204` і для невідомого, і для вже підтвердженого email.

### 3. Avatar upload

1. Заповни `CLD_NAME`, `CLD_API_KEY`, `CLD_API_SECRET`.
2. Login -> скопіюй `access_token`.
3. `PATCH /api/users/me/avatar` з Bearer token і `multipart/form-data` полем `file`.
4. У відповіді має з'явитися `avatar_url`.

Обмеження: тільки `image/*`, максимальний розмір — 5MB.

### 4. Перевірка міграцій

```bash
uv run alembic current
uv run alembic upgrade head
```

Після міграцій таблиця `users` містить поля `email_verified` і `avatar_url`.

### 5. Повторення інфраструктури з теми 10

- CORS: `frontend-cors-demo/index.html`
- Rate limit: 11 запитів до `GET /api/users/me` за хвилину -> `429`
- Redis cache: два однакові `GET /api/todos/?limit=10&offset=0` -> один DB hit у логах
- IP blacklist: `data/blocked_ips.json` -> перезапуск сервера -> `403`
- RBAC: `user_demo`, `mod_demo`, `admin_demo` / `demo1234`

## Структура проєкту

```text
lesson_13/
├── main.py
├── docker-compose.yml
├── data/blocked_ips.json
├── docs/
│   ├── conf.py
│   ├── index.rst
│   └── _build/html/        # зібрана HTML-документація
├── scripts/
│   ├── seed_users.py
│   └── smoke_test.py
├── src/
│   ├── routes/             # auth, users, todos, access
│   ├── services/           # auth, users, todos, cache, email, avatars
│   ├── templates/          # email і pages templates
│   ├── middleware/
│   ├── repository/
│   ├── schemas/
│   ├── entity/models.py
│   └── conf/config.py
├── tests/
│   ├── conftest.py
│   ├── test_api_routes.py
│   ├── test_auth_routes.py
│   └── test_avatars.py
└── frontend-cors-demo/
```

## Типові помилки

| Симптом | Що перевірити |
| --------- | ---------------- |
| `403` на login | email ще не підтверджено |
| Лист не приходить | `MAIL_*`, SMTP-порт, SSL/TLS flags, spam folder |
| Verify link веде не туди | `APP_PUBLIC_URL` |
| `401` на verify | прострочений token або інший `EMAIL_TOKEN_SECRET_KEY` |
| `415` avatar | файл не має `image/*` content type |
| `413` avatar | файл більший за 5MB |
| `502` avatar | `CLD_*` або Cloudinary upload |
| `503` readyz | Postgres або Redis не запущені |
