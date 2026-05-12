# Simple JWT + SQLite + FastAPI

Навчальний мінімальний приклад:

- `POST /register` - реєстрація користувача в SQLite
- `POST /token` - логін, повертає JWT access token
- `GET /public` - публічний маршрут
- `GET /private` - захищений маршрут, потрібен `Bearer` token

## Запуск

З кореня `lesson_09`:

```powershell
uv run fastapi dev base-jwt/main.py
```

Swagger буде тут:

```text
http://127.0.0.1:8000/docs
```

## Перевірка через Swagger

1. Виклич `POST /register`:

```json
{
  "username": "bob",
  "password": "secret123"
}
```

2. Натисни `Authorize` у Swagger.
3. Введи:

```text
username: bob
password: secret123
```

4. Виклич `GET /private`.

## Перевірка через curl

```powershell
curl -X POST http://127.0.0.1:8000/register `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"bob\",\"password\":\"secret123\"}"
```

```powershell
$token = curl -X POST http://127.0.0.1:8000/token `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=bob&password=secret123" | ConvertFrom-Json
```

```powershell
curl http://127.0.0.1:8000/private `
  -H "Authorization: Bearer $($token.access_token)"
```

SQLite база створиться автоматично тут:

```text
base-jwt/app.db
```
