# Розгортання Secured Todo API на Fly.io

Покрокова інструкція для деплою FastAPI-застосунку на [Fly.io](https://fly.io/) з:

- **Postgres** — unmanaged Fly Postgres (НЕ Managed Postgres / `fly mpg`);
- **Redis** — Upstash Redis через `fly redis create` (pay-as-you-go).

> Ця інструкція відповідає реальному деплою проєкту `lesson_15`. Команди можна копіювати один в один, замінивши лише імена ресурсів і значення секретів.

---

## 1. Передумови

| Що потрібно | Перевірка |
|-------------|-----------|
| Акаунт Fly.io | https://fly.io/app/sign-up |
| `flyctl` | `flyctl version` |
| Авторизація | `flyctl auth whoami` |
| Код проєкту локально | каталог `lesson_15` |

Встановлення `flyctl` (Windows, PowerShell):

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

Логін:

```powershell
flyctl auth login
```

---

## 2. Архітектура деплою

```text
Internet
   │
   ▼
lesson-15-todo-api.fly.dev  (FastAPI, Fly Machine, region: fra)
   │
   ├──► lesson-15-db.flycast:5432   (unmanaged Postgres)
   └──► fly-lesson-15-redis.upstash.io:6379   (Upstash Redis)
```

У репозиторії мають бути три файли для деплою (вже додані):

- `Dockerfile` — збірка образу (Python 3.14 + uv);
- `fly.toml` — конфіг Fly.io (порт, VM, release command);
- `.dockerignore` — виключає `.env`, `.venv`, тести тощо.

---

## 3. Змінні середовища

На Fly.io **не** використовується локальний `.env`. Усі значення передаються через **secrets**.

Локально орієнтуйся на `.env.example`. Для продакшену обов'язково зміни:

- `JWT_SECRET_KEY`
- `EMAIL_TOKEN_SECRET_KEY`
- `APP_PUBLIC_URL` → `https://<ім'я-додатку>.fly.dev`
- `CORS_ORIGINS` → додай публічний URL API
- `DB_URL` → формується після attach Postgres (див. крок 6)
- `REDIS_URL` → видається після створення Upstash Redis (крок 4)

---

## 4. Створення Upstash Redis

```powershell
flyctl redis create `
  --name lesson-15-redis `
  --region fra `
  --org personal `
  --no-replicas `
  --enable-eviction `
  --enable-prodpack=false `
  --enable-auto-upgrade=false
```

> **Важливо:** прапорці `--enable-prodpack=false` і `--enable-auto-upgrade=false` потрібні для неінтерактивного режиму (CI, PowerShell без TTY). Без них команда падає з `Error: prompt: non interactive`.

Після успіху CLI виведе рядок на кшталт:

```text
redis://default:<password>@fly-lesson-15-redis.upstash.io:6379
```

**Збережи його** — це значення для секрету `REDIS_URL`.

Перевірка:

```powershell
flyctl redis list
flyctl redis status lesson-15-redis
```

---

## 5. Створення unmanaged Postgres

```powershell
flyctl postgres create `
  --name lesson-15-db `
  --region fra `
  --org personal `
  --initial-cluster-size 1 `
  --vm-size shared-cpu-1x `
  --volume-size 1 `
  --detach
```

Це **unmanaged** Postgres (`fly postgres create`), а не Managed Postgres (`fly mpg`).

CLI виведе credentials (superuser). **Збережи їх** — повторно їх не покаже.

Перевірка:

```powershell
flyctl postgres list
```

---

## 6. Створення Fly-додатку

```powershell
flyctl apps create lesson-15-todo-api --org personal
```

Прив'язка Postgres до додатку (створить БД `todo_app` і користувача):

```powershell
flyctl postgres attach lesson-15-db `
  --app lesson-15-todo-api `
  --database-name todo_app `
  -y
```

CLI додасть секрет `DATABASE_URL`, наприклад:

```text
postgres://lesson_15_todo_api:<password>@lesson-15-db.flycast:5432/todo_app?sslmode=disable
```

### Формування `DB_URL` для asyncpg

Застосунок читає **`DB_URL`**, не `DATABASE_URL`. Для SQLAlchemy + asyncpg потрібен формат:

```text
postgresql+asyncpg://<user>:<password>@lesson-15-db.flycast:5432/todo_app?ssl=disable
```

> Параметр `?ssl=disable` обов'язковий для внутрішнього Fly Postgres. Без нього Alembic падає з `ConnectionResetError` під час TLS handshake.

---

## 7. Встановлення secrets

Підстав свої значення замість `<...>`:

```powershell
flyctl secrets set -a lesson-15-todo-api `
  DB_URL="postgresql+asyncpg://<db_user>:<db_password>@lesson-15-db.flycast:5432/todo_app?ssl=disable" `
  REDIS_URL="redis://default:<redis_password>@fly-lesson-15-redis.upstash.io:6379" `
  JWT_SECRET_KEY="<довгий-випадковий-секрет>" `
  JWT_ALGORITHM="HS256" `
  ACCESS_TOKEN_EXPIRE_MINUTES="15" `
  REFRESH_TOKEN_EXPIRE_DAYS="7" `
  CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:5500,https://lesson-15-todo-api.fly.dev" `
  RATE_LIMIT_ME="10/minute" `
  CACHE_TTL_SECONDS="60" `
  BLOCKED_IPS_FILE="data/blocked_ips.json" `
  EMAIL_TOKEN_SECRET_KEY="<email-token-secret>" `
  EMAIL_VERIFY_EXPIRE_HOURS="24" `
  APP_PUBLIC_URL="https://lesson-15-todo-api.fly.dev" `
  MAIL_USERNAME="<smtp-user>" `
  MAIL_PASSWORD="<smtp-password>" `
  MAIL_FROM="<from-email>" `
  MAIL_FROM_NAME="Todo API" `
  MAIL_SERVER="smtp.meta.ua" `
  MAIL_PORT="465" `
  MAIL_STARTTLS="False" `
  MAIL_SSL_TLS="True" `
  MAIL_USE_CREDENTIALS="True" `
  MAIL_VALIDATE_CERTS="True" `
  CLD_NAME="<cloudinary-cloud>" `
  CLD_API_KEY="<cloudinary-key>" `
  CLD_API_SECRET="<cloudinary-secret>"
```

Перевірка:

```powershell
flyctl secrets list -a lesson-15-todo-api
```

---

## 8. Деплой

З кореня проєкту:

```powershell
cd I:\WebDir\bachelor_pythonweb\lesson_15
flyctl deploy --ha=false
```

Що відбувається:

1. Збірка Docker-образу (remote builder Depot);
2. `release_command`: `uv run alembic upgrade head` — міграції БД;
3. Запуск Machine у регіоні `fra`;
4. Призначення URL `https://lesson-15-todo-api.fly.dev`.

Моніторинг під час деплою:

```text
https://fly.io/apps/lesson-15-todo-api/monitoring
```

---

## 9. Seed користувачів (опційно)

```powershell
flyctl ssh console -a lesson-15-todo-api -C "uv run python scripts/seed_users.py"
```

Створює:

| Login | Role | Password |
|-------|------|----------|
| `user_demo` | user | `demo1234` |
| `mod_demo` | moderator | `demo1234` |
| `admin_demo` | admin | `demo1234` |

---

## 10. Перевірка після деплою

```powershell
curl https://lesson-15-todo-api.fly.dev/healthz
curl https://lesson-15-todo-api.fly.dev/readyz
curl https://lesson-15-todo-api.fly.dev/
```

Очікувані відповіді:

```json
{"status":"ok","message":"Application is running"}
{"status":"ok","message":"Application is ready (DB + Redis)"}
{"message":"TODO Application v1.0 (lesson 10)"}
```

Swagger UI:

```text
https://lesson-15-todo-api.fly.dev/docs
```

---

## 11. Повторний деплой (оновлення коду)

Після змін у коді:

```powershell
cd I:\WebDir\bachelor_pythonweb\lesson_15
flyctl deploy --ha=false
```

При зміні секретів — спочатку `flyctl secrets set ...`, потім redeploy (або Fly перезапустить machines автоматично).

---

## 12. Корисні команди

```powershell
# Логи
flyctl logs -a lesson-15-todo-api

# Статус machines
flyctl status -a lesson-15-todo-api

# SSH у контейнер
flyctl ssh console -a lesson-15-todo-api

# Ручний запуск міgraцій
flyctl ssh console -a lesson-15-todo-api -C "uv run alembic upgrade head"

# Postgres console
flyctl postgres connect -a lesson-15-db

# Redis console
flyctl redis connect lesson-15-redis

# Список ресурсів
flyctl apps list
flyctl postgres list
flyctl redis list
```

---

## 13. Конфігурація `fly.toml` (довідка)

```toml
app = 'lesson-15-todo-api'
primary_region = 'fra'

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = 'stop'
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = '512mb'
  cpu_kind = 'shared'
  cpus = 1

[deploy]
  release_command = 'uv run alembic upgrade head'
```

- `auto_stop_machines = 'stop'` — machine зупиняється без трафіку (економія). Перший запит після простою може бути повільнішим (cold start).
- Щоб API був завжди online: `min_machines_running = 1`.

---

## 14. Орієнтовна вартість

| Ресурс | План | Орієнтовно |
|--------|------|------------|
| API Machine | shared-cpu-1x, 512MB, auto-stop | оплата за uptime |
| Postgres | unmanaged, 1 node, 1GB volume | ~$2–5/міс |
| Redis | Upstash pay-as-you-go | $0.20 / 100K команд |

---

## 15. Типові помилки

| Симптом | Причина | Рішення |
|---------|---------|---------|
| `Error: prompt: non interactive` при `fly redis create` | CLI чекає відповідь про ProdPack | Додай `--enable-prodpack=false --enable-auto-upgrade=false` |
| `ConnectionResetError` у release_command | asyncpg намагається SSL до Fly Postgres | Додай `?ssl=disable` до `DB_URL` |
| `503` на `/readyz` | Redis або Postgres недоступні | Перевір secrets, `flyctl postgres list`, `flyctl redis status` |
| Лист verify веде на localhost | Невірний `APP_PUBLIC_URL` | Встанови `https://<app>.fly.dev` |
| `release_command failed` | БД ще не attach або невірний `DB_URL` | Повтори кроки 6–7 |

---

## 16. Повний чеклист (коротко)

1. `flyctl auth login`
2. `flyctl redis create ...` → зберегти `REDIS_URL`
3. `flyctl postgres create ...` → зберегти credentials
4. `flyctl apps create lesson-15-todo-api`
5. `flyctl postgres attach lesson-15-db --app lesson-15-todo-api --database-name todo_app -y`
6. `flyctl secrets set ...` (включно з `DB_URL` + `?ssl=disable`)
7. `flyctl deploy --ha=false`
8. `flyctl ssh console ... seed_users.py` (опційно)
9. Перевірити `/healthz`, `/readyz`, `/docs`

---

## Ресурси

- Fly.io docs: https://fly.io/docs/
- Fly Postgres (unmanaged): https://fly.io/docs/postgres/
- Upstash Redis on Fly: https://fly.io/docs/reference/redis/
- flyctl redis create: https://fly.io/docs/flyctl/redis-create/
