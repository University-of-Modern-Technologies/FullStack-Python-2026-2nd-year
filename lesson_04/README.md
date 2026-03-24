# Lesson 04: Concurrency Examples

Набір навчальних прикладів по конкурентності в Python 3.14.

Рекомендований порядок вивчення:
1. `threads_example` (простий старт з синхронізацією в одному процесі)
2. `process_example` (ізоляція пам'яті + multiprocessing primitives)
3. `async_example` (cooperative concurrency через event loop)

## Запуск прикладів

З кореня `lesson_04` встанови залежності через `uv`, і запускай потрібний файл:

```powershell
uv sync

uv run python threads_example\01-example.py
uv run python process_example\01-example.py
uv run python async_example\01-example.py
```

## Threads examples (потоки)

Коли використовувати: I/O-bound задачі, lightweight concurrency, робота в межах одного процесу.

- `01-example.py` - базовий запуск `Thread` і старт worker-функцій.
- `02-example.py` - запуск декількох потоків у циклі.
- `03-example-lock.py` - `Lock`: взаємне виключення для критичних секцій.
- `04-example-event.py` - `Event`: сигнальна синхронізація (`wait` / `set`).
- `05-example-condition.py` - `Condition`: очікування умови + `notify_all`.
- `06-example-semaphore.py` - `Semaphore`: обмеження одночасного доступу.
- `07-example-barrier.py` - `Barrier`: точка синхронізації групи потоків.

## Process examples (процеси)

Коли використовувати: CPU-bound задачі, обхід GIL, ізоляція пам'яті між воркерами.

- `01-example.py` - базовий запуск процесів через `Process`.
- `02-example.py` - старт декількох процесів і контроль статусів.
- `03-example-join.py` - `join()`: очікування завершення дочірніх процесів.
- `04-example-event.py` - `multiprocessing.Event` для міжпроцесного сигналу.
- `05-example-condition.py` - `Condition` між процесами (master/worker).
- `06-example-semaphore.py` - `Semaphore` для ліміту паралельних процесів.
- `07-example-barrier.py` - `Barrier` для узгодженого проходу етапів.
- `08-example-pool.py` - `Pool` + `apply_async` + callback.

## Async examples (`asyncio`)

Коли використовувати: велика кількість I/O операцій (HTTP, БД, сокети), де важлива масштабованість на одному потоці.

### Базові патерни

- `01-example.py` - базовий `async/await`, послідовні корутини.
- `02-example.py` - `create_task`, керування життєвим циклом задач, `cancel`.
- `03-example-gather.py` - `asyncio.gather` (успішний сценарій).
- `04-example-gather-errors.py` - `gather(return_exceptions=True)` для збору помилок.

### Примітиви синхронізації в `asyncio`

- `05-example-event.py` - `asyncio.Event`.
- `06-example-condition.py` - `asyncio.Condition` + `wait_for`.
- `07-example-semaphore.py` - `asyncio.Semaphore`.
- `08-example-barrier.py` - `asyncio.Barrier`.

### Керування задачами і часом

- `09-example-taskgroup.py` - `TaskGroup`, fail-fast при помилці.
- `10-example-timeout.py` - `asyncio.timeout` і `asyncio.wait_for`.
- `11-example-as-completed.py` - `as_completed`: результати в порядку завершення.
- `12-example-future-task.py` - `Future` + `Task`, ручне `set_result/set_exception`.
- `15-example-wait.py` - `asyncio.wait` режими: `ALL_COMPLETED` / `FIRST_COMPLETED`.

### Інтеграція blocking коду і HTTP клієнти

- `13-example-bounds.py` - `run_in_executor` для blocking / CPU задач.
- `14-example-to-thread.py` - `asyncio.to_thread` для sync I/O без блокування loop.
- `16-example-aiohttp-client.py` - async HTTP запит через `aiohttp`.
- `17-example-httpx-client.py` - async HTTP запит через `httpx`, параметр дати (за замовчуванням сьогодні).
- `timing.py` - декоратори для заміру часу (`async_timed`, `sync_timed`).
