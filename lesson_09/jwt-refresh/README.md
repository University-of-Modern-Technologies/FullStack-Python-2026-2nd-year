# JWT Refresh + SQLite + FastAPI

Це продовження базового JWT прикладу:

- `POST /register` - реєстрація користувача в SQLite
- `POST /token` - логін, повертає `access_token` і `refresh_token`
- `POST /refresh` - приймає `refresh_token`, повертає новий `access_token`
- `GET /public` - публічний маршрут
- `GET /private` - захищений маршрут, потрібен `access_token`

## Ідея

`access_token` живе коротко і використовується для запитів до API.

`refresh_token` живе довше і використовується тільки для отримання нового `access_token`. Це не JWT, а випадковий opaque token.

У БД зберігається не сам refresh token, а його hash:

```text
refresh_token -> sha256(refresh_token) -> refresh_tokens.token_hash
```

Якщо БД витече, готові refresh tokens не будуть лежати там відкритим текстом.

В `access_token` є claim `type`:

```json
{
  "type": "access"
}
```

Тому `/private` приймає тільки access JWT. `/refresh` працює окремо через lookup refresh token hash у БД.

## Запуск

З кореня `lesson_09`:

```powershell
uv run fastapi dev jwt-refresh/main.py
```

Swagger:

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

2. Виклич `POST /token` з:

```text
username: bob
password: secret123
```

У відповіді буде:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

3. Натисни `Authorize` у Swagger і встав `access_token`.
4. Виклич `GET /private`.
5. Виклич `POST /refresh` і передай `refresh_token`:

```json
{
  "refresh_token": "..."
}
```

6. Отриманий новий `access_token` можна знову використати для `/private`.

## Перевірка через curl

```powershell
curl -X POST http://127.0.0.1:8000/register `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"bob\",\"password\":\"secret123\"}"
```

```powershell
$tokens = curl -X POST http://127.0.0.1:8000/token `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=bob&password=secret123" | ConvertFrom-Json
```

```powershell
curl http://127.0.0.1:8000/private `
  -H "Authorization: Bearer $($tokens.access_token)"
```

```powershell
$newAccess = curl -X POST http://127.0.0.1:8000/refresh `
  -H "Content-Type: application/json" `
  -d "{`"refresh_token`":`"$($tokens.refresh_token)`"}" | ConvertFrom-Json
```

```powershell
curl http://127.0.0.1:8000/private `
  -H "Authorization: Bearer $($newAccess.access_token)"
```

SQLite база створиться автоматично тут:

```text
jwt-refresh/app.db
```
