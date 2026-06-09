# IpBlockMiddleware — опис

Файл: `src/middleware/ip_block.py`  
Дані: `data/blocked_ips.json` (шлях у `BLOCKED_IPS_FILE`).

## Формат JSON

```json
[
  { "ip": "203.0.113.50", "reason": "Підозріла активність" }
]
```

- масив об'єктів
- `ip` — рядок (як бачить сервер у `request.client.host`)
- `reason` — текст для відповіді 403

Файл читається **при старті** процесу. Після зміни JSON — перезапусти `fastapi dev`.

## Поведінка

1. IP у списку → `403` + JSON `{ "error", "ip", "reason" }`
2. Інакше → `call_next(request)`

Немає файлу / битий JSON → порожній blacklist, warning у логах.

## Порядок middleware (LIFO)

У `main.py`:

1. `CORSMiddleware` — реєструється першим (ближче до app)
2. `IpBlockMiddleware` — другим (зовнішній на request)

На request: **IP перевірка → CORS → … → роут**.

## Конфіг

| Змінна | За замовч. |
|--------|------------|
| `BLOCKED_IPS_FILE` | `data/blocked_ips.json` |

Відносний шлях — від кореня проєкту (`lesson_10/`).

## Лаба

1. Додай у JSON IP, з якого тестуєш (або тестуй з `203.0.113.50` через curl `--interface` / mock — простіше тимчасово підставити `127.0.0.1` у файл для перевірки)
2. `GET /healthz` → 403 з `reason`

**Увага:** блок `127.0.0.1` заблокує локальні запити до Swagger.

## Обмеження (лаба)

- без admin API для зміни списку
- без hot-reload після edit JSON
- без `X-Forwarded-For` (за проксі треба окрема логіка)
