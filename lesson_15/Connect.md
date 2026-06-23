# Підключення до інфраструктури на Fly.io

Інструкція для роботи з продакшен-середовищем проєкту `lesson_15`:

| Ресурс | Ім'я на Fly.io |
|--------|----------------|
| API (FastAPI) | `lesson-15-todo-api` |
| Postgres | `lesson-15-db` |
| Redis (Upstash) | `lesson-15-redis` |

> Передумова: встановлений і авторизований `flyctl` (`flyctl auth whoami`).

---

## 1. Postgres через DBeaver

Postgres на Fly.io **не відкритий в інтернет**. Підключення з DBeaver робиться через **локальний тунель** `fly proxy`.

### Крок 1. Запусти proxy (окреме вікно PowerShell)

Якщо локально Postgres не займає порт `5432`:

```powershell
flyctl proxy 5432:5432 -a lesson-15-db
```

Якщо порт `5432` зайнятий (наприклад, локальний Docker Postgres):

```powershell
flyctl proxy 15432:5432 -a lesson-15-db
```

Очікуваний вивід:

```text
Proxying local port 15432 to remote [lesson-15-db.internal]:5432
```

**Не закривай це вікно** — поки proxy працює, DBeaver підключається до `localhost`.

### Крок 2. Дізнайся логін і пароль

#### Варіант A — superuser `postgres` (адмін-доступ)

```powershell
flyctl ssh console -a lesson-15-db -C "printenv OPERATOR_PASSWORD"
```

Пароль виведеться в консоль (можливе повідомлення `The handle is invalid` — **ігноруй**, пароль уже показано).

#### Варіант B — користувач додатку `lesson_15_todo_api`

Пароль зберігається в секреті `DATABASE_URL` API-додатку. Якщо machine зупинена (auto-stop), спочатку «розбуди» її:

```powershell
curl https://lesson-15-todo-api.fly.dev/healthz
```

Потім:

```powershell
flyctl ssh console -a lesson-15-todo-api -C "printenv DATABASE_URL"
```

Рядок матиме вигляд:

```text
postgres://lesson_15_todo_api:<password>@lesson-15-db.flycast:5432/todo_app?sslmode=disable
```

### Крок 3. Налаштування DBeaver

1. **Database → New Database Connection → PostgreSQL**
2. Вкладка **Main**:

| Поле | Значення |
|------|----------|
| Host | `localhost` |
| Port | `5432` або `15432` (як у proxy) |
| Database | `todo_app` |
| Username | `lesson_15_todo_api` або `postgres` |
| Password | з кроку 2 |

3. Вкладка **Driver properties** (або **SSL**):
   - **SSL mode** → `disable`  
   (Fly Postgres через proxy не потребує TLS на локальному підключенні)

4. **Test Connection → Finish**

### Альтернатива — psql без DBeaver

Окреме вікно proxy не потрібне — `fly postgres connect` сам відкриває сесію:

```powershell
flyctl postgres connect -a lesson-15-db -d todo_app -u lesson_15_todo_api
```

Superuser:

```powershell
flyctl postgres connect -a lesson-15-db
```

### Корисні SQL-запити

```sql
-- список таблиць
\dt

-- користувачі
SELECT id, username, email, role, email_verified FROM users;

-- todos
SELECT id, title, user_id, is_completed FROM todos LIMIT 20;
```

---

## 2. Консоль сервера (SSH у контейнер API)

### Інтерактивна shell-сесія

```powershell
flyctl ssh console -a lesson-15-todo-api
```

Потрапиш у Linux-контейнер застосунку (`/app`). Приклади команд всередині:

```bash
# змінні середовища (без виводу секретів у логи — обережно)
printenv APP_PUBLIC_URL
printenv DATABASE_URL

# міграції вручну
uv run alembic current
uv run alembic upgrade head

# seed користувачів
uv run python scripts/seed_users.py

# перегляд файлів
ls -la
cat data/blocked_ips.json
```

Вихід: `exit`

### Одна команда без інтерактивної сесії

```powershell
flyctl ssh console -a lesson-15-todo-api -C "uv run alembic current"
```

```powershell
flyctl ssh console -a lesson-15-todo-api -C "uv run python scripts/seed_users.py"
```

### Якщо machine зупинена

При `auto_stop_machines = "stop"` machine спить без трафіку. Розбуди:

```powershell
curl https://lesson-15-todo-api.fly.dev/healthz
```

або:

```powershell
flyctl machine start -a lesson-15-todo-api
```

Перевір статус:

```powershell
flyctl status -a lesson-15-todo-api
flyctl machines list -a lesson-15-todo-api
```

### Логи без SSH

```powershell
flyctl logs -a lesson-15-todo-api
```

---

## 3. Redis (Upstash)

Redis доступний **лише всередині Fly-організації** (private URL). З локальної машини — через `flyctl`.

### Варіант A — redis-cli (рекомендовано)

```powershell
flyctl redis connect -o personal
```

CLI запропонує вибрати базу → обери `lesson-15-redis`.  
Відкриється інтерактивна консоль на `127.0.0.1:16379`:

```text
127.0.0.1:16379> PING
PONG
127.0.0.1:16379> KEYS todos:list:*
127.0.0.1:16379> GET todos:list:1:10:0
127.0.0.1:16379> TTL todos:list:1:10:0
127.0.0.1:16379> exit
```

### Варіант B — веб-консоль Upstash

```powershell
flyctl redis dashboard personal
```

Відкриється браузер з Upstash Console: ключі, метрики, connection string.

### Варіант C — переглянути URL підключення

```powershell
flyctl redis status lesson-15-redis
```

Поле **Private URL**:

```text
redis://default:<password>@fly-lesson-15-redis.upstash.io:6379
```

> Цей URL працює **з Fly Machines** (секрет `REDIS_URL` у додатку).  
> Напряму з домашнього ПК без proxy/WireGuard — **не працює**.

### Варіант D — GUI-клієнт (RedisInsight, Another Redis Desktop Manager)

1. В одному терміналі запусти proxy через connect (тримай сесію відкритою):

   ```powershell
   flyctl redis connect -o personal
   ```

   Fly проксує Redis на локальний порт (зазвичай `16379`).

2. У GUI-клієнті:

| Поле | Значення |
|------|----------|
| Host | `127.0.0.1` |
| Port | `16379` |
| Password | з `flyctl redis status lesson-15-redis` (частина URL після `default:`) |
| Username | `default` (якщо клієнт питає) |
| SSL/TLS | **вимкнено** |

### Типові Redis-ключі в проєкті

Застосунок кешує списки todo:

```text
todos:list:<user_id>:<limit>:<offset>
```

Приклад:

```text
todos:list:1:10:0
```

---

## 4. Швидка шпаргалка

```powershell
# --- Postgres → DBeaver ---
flyctl proxy 15432:5432 -a lesson-15-db          # тримати відкритим
flyctl ssh console -a lesson-15-db -C "printenv OPERATOR_PASSWORD"

# --- Postgres → psql ---
flyctl postgres connect -a lesson-15-db -d todo_app

# --- API console ---
flyctl ssh console -a lesson-15-todo-api
flyctl logs -a lesson-15-todo-api

# --- Redis ---
flyctl redis connect -o personal
flyctl redis status lesson-15-redis
flyctl redis dashboard personal
```

---

## 5. Типові проблеми

| Симптом | Причина | Рішення |
|---------|---------|---------|
| DBeaver: `Connection reset` | Proxy не запущений або невірний `-a` | Перевір `flyctl proxy ... -a lesson-15-db` (саме **db**, не api) |
| DBeaver: `database "todo_app" does not exist` | Невірна назва БД | Вкажи `todo_app`, не `lesson-15-todo-api` |
| `app has no started VMs` | Machine спить (auto-stop) | `curl .../healthz` або `flyctl machine start` |
| Redis GUI не підключається | Намагаєшся підключитись до Upstash URL напряму | Використовуй `fly redis connect` + `localhost:16379` |
| `The handle is invalid` після SSH-команди | Особливість flyctl на Windows | Команда часто **виконалась успішно** — дивись вивід вище помилки |
| Забув пароль Postgres | Credentials не показуються повторно | `printenv OPERATOR_PASSWORD` на `lesson-15-db` або reset user |

---

## 6. Безпека

- Не коміть паролі та connection string у git.
- На спільному ПК закривай proxy-вікно після роботи з DBeaver.
- Superuser `postgres` використовуй лише для адмін-задач; для перегляду даних достатньо `lesson_15_todo_api`.

---

## Ресурси

- Fly Postgres + flyctl: https://fly.io/docs/postgres/connecting/connecting-with-flyctl/
- Fly proxy: https://fly.io/docs/flyctl/proxy/
- Upstash Redis on Fly: https://fly.io/docs/reference/redis/
- DBeaver: https://dbeaver.io/
