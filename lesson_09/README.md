# Lesson 09: JWT Auth у FastAPI

У цьому уроці є три приклади авторизації у FastAPI:

- `base-jwt` - мінімальний JWT access token приклад з SQLite.
- `jwt-refresh` - JWT access token + opaque refresh token з SQLite.
- `full-app` - повний Todo API з PostgreSQL, Alembic, user-owned todos, access JWT і refresh tokens у БД.

## Вимоги

- Python 3.14+
- uv
- PostgreSQL для `full-app`

## Встановлення залежностей

З кореня `lesson_09`:

```bash
uv sync
```

## base-jwt

Мінімальний приклад:

- `POST /register`
- `POST /token`
- `GET /public`
- `GET /private`

Запуск:

```bash
uv run fastapi dev base-jwt/main.py
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

SQLite база створюється автоматично:

```text
base-jwt/app.db
```

## jwt-refresh

Приклад з refresh token:

- `access_token` - JWT
- `refresh_token` - opaque random token
- у БД зберігається тільки `sha256(refresh_token)`

Маршрути:

- `POST /register`
- `POST /token`
- `POST /refresh`
- `GET /public`
- `GET /private`

Запуск:

```bash
uv run fastapi dev jwt-refresh/main.py
```

SQLite база створюється автоматично:

```text
jwt-refresh/app.db
```

## full-app

Повний Todo API:

- async SQLAlchemy
- PostgreSQL
- Alembic migrations
- `routes -> services -> repository`
- auth через `pwdlib[argon2]` + PyJWT
- todos належать користувачу
- refresh tokens зберігаються в БД як hash

### Налаштування

Створи `.env` з прикладу:

```bash
cp full-app/.env.example full-app/.env
```

Онови PostgreSQL credentials у:

```text
full-app/.env
```

### Міграції

З папки `full-app`:

```bash
uv run alembic upgrade head
```

### Запуск

З папки `full-app`:

```bash
uv run fastapi dev main.py
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### Auth Endpoints

- `POST /api/auth/register` - реєстрація
- `POST /api/auth/login` - логін, повертає `access_token` і `refresh_token`
- `POST /api/auth/refresh` - новий access token через refresh token
- `POST /api/auth/logout` - видалити refresh token з БД
- `GET /api/auth/me` - поточний користувач

### Todo Endpoints

Усі todo маршрути потребують:

```text
Authorization: Bearer <access_token>
```

Маршрути:

- `GET /api/todos/`
- `GET /api/todos/{todo_id}`
- `POST /api/todos/`
- `PUT /api/todos/{todo_id}`
- `PATCH /api/todos/{todo_id}`
- `DELETE /api/todos/{todo_id}`

Користувач бачить і змінює тільки свої todos.

### Kubernetes-style Health Probes

- `GET /healthz` - застосунок живий
- `GET /readyz` - застосунок готовий, БД доступна

## Корисний Flow для Swagger

1. `POST /api/auth/register`
2. `POST /api/auth/login`
3. Натиснути `Authorize` і вставити `access_token`
4. `POST /api/todos/`
5. `GET /api/todos/`
6. `POST /api/auth/refresh`
7. Замінити access token на новий
8. `POST /api/auth/logout`
