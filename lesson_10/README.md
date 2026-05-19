# Lesson 10: Безпека та продуктивність backend

Розширення Todo API з lesson_09: env, rate limiting, CORS, Redis-кеш, RBAC, IP blacklist.

## Вимоги

- Python 3.14+
- uv
- Docker (Postgres + Redis)

## Швидкий старт

```bash
cp .env.example .env          # до docker compose (POSTGRES_* з .env)
uv sync
docker compose up -d
uv run alembic upgrade head
uv run python scripts/seed_users.py
uv run fastapi dev main.py
```

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

**Seed-користувачі** (`scripts/seed_users.py`): `user_demo`, `mod_demo`, `admin_demo` — пароль `demo1234`.

## Архітектура

```text
HTTP → middleware (IP, CORS) → routes → services → repository → Postgres
                                              ↘ cache (Redis)
```

| Шар | Папка | Роль |
|-----|-------|------|
| Routes | `src/routes/` | HTTP, `Depends`, `response_model` — **без** репозиторіїв |
| **Services** | `src/services/` | **Бізнес-логіка** |
| Repository | `src/repository/` | SQL / ORM |
| Middleware | `src/middleware/` | IP blacklist, CORS у `main.py` |
| Schemas | `src/schemas/` | Pydantic: `user.py`, `auth.py`, `todo.py` |

### Документація сервісів і middleware

Основна логіка — у **services** (детальний розбір у `.md` поруч із кодом):

| Модуль | Опис |
|--------|------|
| [src/services/auth.md](src/services/auth.md) | JWT, login/refresh/logout, `get_current_*` (роль у токені) |
| [src/services/todos.md](src/services/todos.md) | CRUD todos, `get_todos` vs `get_all_todos`, invalidate кешу |
| [src/services/users.md](src/services/users.md) | Список users, зміна ролі (admin) |
| [src/services/cache.md](src/services/cache.md) | Redis-кеш списку todos |
| [src/middleware/ip_block.md](src/middleware/ip_block.md) | Blacklist IP з `data/blocked_ips.json` |

### Порядок обробки запиту (middleware)

1. IP blacklist — `src/middleware/ip_block.py`
2. CORS — `main.py`
3. Rate limit — `@limiter.limit` на `/api/auth/me`
4. Auth / RBAC — `Depends(get_current_user | moderator | admin)`
5. Route handler

## Тема 10 — огляд

| Тема | Код | Документація | Перевірка |
|------|-----|--------------|-----------|
| Env | `src/conf/config.py`, `.env` | — | змінити `JWT_SECRET_KEY` → старий token `401` |
| IP blacklist | `data/blocked_ips.json`, `src/middleware/ip_block.py` | [ip_block.md](src/middleware/ip_block.md) | IP у JSON → `403` |
| CORS | `main.py`, `frontend-cors-demo/` | — | fetch з іншого origin |
| Rate limit | `src/limiter.py`, `src/routes/auth.py` | [auth.md](src/services/auth.md) | 11× `GET /api/auth/me` → `429` |
| Redis cache | `src/services/cache.py`, `todos.py` | [cache.md](src/services/cache.md), [todos.md](src/services/todos.md) | 2× `GET /api/todos/` → один `DB hit` |
| RBAC | `src/routes/access.py`, `services/users.py` | [users.md](src/services/users.md), [auth.md](src/services/auth.md) | див. лабу §6 |

## API

### Auth (`src/routes/auth.py` → [auth.md](src/services/auth.md))

| Метод | Шлях | Примітка |
|-------|------|----------|
| POST | `/api/auth/register` | |
| POST | `/api/auth/login` | form OAuth2 |
| POST | `/api/auth/refresh` | body: `refresh_token` |
| POST | `/api/auth/logout` | Bearer + `refresh_token`, свій refresh |
| GET | `/api/auth/me` | rate limit, роль з JWT |

### Todos (`src/routes/todos.py` → [todos.md](src/services/todos.md))

`GET/POST/PUT/PATCH/DELETE /api/todos/*` — Bearer, лише **свої** todos.

### RBAC demo (`src/routes/access.py`)

Потрібен seed + login. Префікс `/api/access`:

| Метод | Шлях | Хто |
|-------|------|-----|
| GET | `/user` | будь-який з токеном |
| GET | `/moderator/todos` | moderator, admin |
| GET | `/admin/users` | admin |
| PATCH | `/admin/users/{id}/role` | admin |

### Health

- `GET /healthz` — процес живий
- `GET /readyz` — Postgres + Redis

## Лабораторні сценарії

### 1. Конфігурація (.env)

`JWT_SECRET_KEY` → перезапуск → старий access → `401`.

### 2. Rate limiting

`user_demo` / `demo1234` → 11× `GET /api/auth/me` → 11-й `429`.

### 3. CORS

`frontend-cors-demo/index.html` (Live Server), origin у `CORS_ORIGINS`. Кнопка → `GET /healthz`.

### 4. Redis cache

Логін → двічі `GET /api/todos/?limit=10&offset=0` → у логах один `DB hit: get_todos`.

### 5. IP blacklist

`data/blocked_ips.json` — див. [ip_block.md](src/middleware/ip_block.md). Після зміни файлу — **перезапуск** сервера.

### 6. RBAC

Перед тестом: `uv run python scripts/seed_users.py` (якщо ще не робив).

| Логін | Пароль | Роль |
|-------|--------|------|
| user_demo | demo1234 | user |
| mod_demo | demo1234 | moderator |
| admin_demo | demo1234 | admin |

1. Login → скопіюй `access_token`
2. `user_demo` → `GET /api/access/admin/users` → **403**
3. `mod_demo` → `GET /api/access/moderator/todos` → **200**
4. `admin_demo` → `GET /api/access/admin/users` → **200**

Після `PATCH .../role` нова роль у access лише після `login` або `refresh`.

## Структура проєкту

```text
lesson_10/
├── main.py                 # FastAPI, middleware, routers
├── data/blocked_ips.json
├── scripts/seed_users.py
├── src/
│   ├── routes/             # auth, todos, access
│   ├── services/           # бізнес-логіка (+ *.md)
│   ├── middleware/         # ip_block (+ ip_block.md)
│   ├── repository/
│   ├── schemas/
│   ├── entity/models.py
│   └── conf/config.py
└── frontend-cors-demo/
```

## Типові помилки

| Симптом | Що перевірити |
|---------|----------------|
| **401** на захищених | Bearer, новий token після зміни `JWT_SECRET_KEY` |
| **403** RBAC | роль у JWT; після зміни ролі — refresh/login |
| **403** IP | `data/blocked_ips.json`, перезапуск |
| **429** | `app.state.limiter`, `Request` на `/me` |
| **CORS** | origin з `http://` у `CORS_ORIGINS` |
| **503** readyz | `docker compose up -d` |
| **compose без БД** | спочатку `cp .env.example .env` |
