# Lesson 14: RabbitMQ, Pub/Sub, Celery, MongoEngine

У цьому проєкті зібрано кілька прикладів роботи з чергами повідомлень і фоновими задачами.

Основні теми:

- `RabbitMQ` як брокер повідомлень.
- `pika` як Python-клієнт для RabbitMQ.
- producer/consumer модель.
- звичайна черга повідомлень.
- черга задач з ручним підтвердженням.
- pub/sub через `fanout exchange`.
- Celery як високорівнева система фонових задач.
- MongoEngine як ODM для MongoDB.

## Головна ідея RabbitMQ

RabbitMQ - це посередник між кодом, який створює повідомлення, і кодом, який ці повідомлення обробляє.

Є дві типові ролі:

- `producer` - створює повідомлення і відправляє його в RabbitMQ.
- `consumer` - підключається до RabbitMQ, чекає повідомлення і обробляє його.

Спрощена схема:

```text
producer -> RabbitMQ -> consumer
```

Але всередині RabbitMQ зазвичай є ще дві важливі сутності:

- `exchange` - приймає повідомлення від producer-а і вирішує, куди його направити.
- `queue` - черга, в якій повідомлення лежить, поки consumer його не забере.

Більш точна схема:

```text
producer -> exchange -> queue -> consumer
```

## Основні поняття

### Connection

```python
connection = pika.BlockingConnection(...)
```

Це TCP-з'єднання з RabbitMQ.

У локальних прикладах використовується:

```python
host="localhost"
port=5672
credentials=pika.PlainCredentials("guest", "guest")
```

Тобто код очікує, що RabbitMQ запущений локально і доступний на порту `5672`.

### Channel

```python
channel = connection.channel()
```

Канал - це логічний канал спілкування всередині одного connection. Через нього ми створюємо черги, exchange-и, публікуємо і читаємо повідомлення.

### Queue

```python
channel.queue_declare(queue="hello")
```

Черга зберігає повідомлення. Якщо consumer зараз не запущений, повідомлення може лежати в черзі і чекати.

Якщо викликати `queue_declare` кілька разів з однаковими параметрами, це нормально. RabbitMQ просто переконається, що така черга існує.

### Exchange

Exchange приймає повідомлення від producer-а і маршрутизує його в одну або кілька черг.

У проєкті є два типи exchange:

- `direct` - відправляє повідомлення в чергу за точним `routing_key`.
- `fanout` - розсилає повідомлення в усі прив'язані черги.

### Routing key

`routing_key` - це ключ маршрутизації. Для `direct exchange` він повинен збігатися з ключем, з яким черга прив'язана до exchange.

Наприклад:

```python
channel.queue_bind(
    exchange="bachelor exchange",
    queue="bachelor",
    routing_key="bachelor",
)
```

І тоді producer має публікувати так:

```python
channel.basic_publish(
    exchange="bachelor exchange",
    routing_key="bachelor",
    body=...
)
```

Якщо ключі не збігаються, `direct exchange` не доставить повідомлення в цю чергу.

### Ack

`ack` - це підтвердження, що consumer успішно обробив повідомлення.

Є два режими:

```python
auto_ack=True
```

RabbitMQ вважає повідомлення обробленим одразу після доставки consumer-у.

```python
ch.basic_ack(delivery_tag=method.delivery_tag)
```

Consumer сам вручну підтверджує обробку. Це надійніше для задач, бо якщо worker впаде під час роботи, RabbitMQ може повернути повідомлення в чергу.

## 01_hello_world

Файли:

- `01_hello_world/producer.py`
- `01_hello_world/consumer.py`

Це найпростіший приклад.

Схема:

```text
producer -> queue "hello" -> consumer
```

Тут не створюється власний exchange. Використовується стандартний exchange RabbitMQ з назвою `""`.

### Producer

```python
channel.queue_declare(queue='hello')

message = b'Hello World!!'
channel.basic_publish(exchange='', routing_key='hello', body=message)
```

Що тут відбувається:

1. Створюється або перевіряється черга `hello`.
2. Створюється байтове повідомлення `b'Hello World!!'`.
3. Повідомлення публікується в стандартний exchange `""`.
4. `routing_key='hello'` означає: поклади повідомлення в чергу `hello`.

Для стандартного exchange правило просте:

```text
routing_key == назва черги
```

### Consumer

```python
channel.queue_declare(queue='hello')
```

Consumer теж оголошує чергу. Це захист від ситуації, коли consumer запустили раніше за producer.

```python
def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
```

`callback` - це функція, яку RabbitMQ викликає для кожного отриманого повідомлення.

```python
channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)
channel.start_consuming()
```

`basic_consume` каже: слухай чергу `hello` і для кожного повідомлення викликай `callback`.

`start_consuming()` запускає нескінченне очікування повідомлень.

### Як запускати

У першому терміналі:

```bash
python 01_hello_world/consumer.py
```

У другому терміналі:

```bash
python 01_hello_world/producer.py
```

Очікуваний результат у consumer:

```text
[*] Waiting for messages. To exit press CTRL+C
[x] Received Hello World!!
```

### Для чого цей приклад

Він показує мінімальну producer/consumer модель:

```text
один producer -> одна черга -> один consumer
```

## 02_task

Файли:

- `02_task/producer.py`
- `02_task/consumer.py`

Це приклад черги задач.

Схема:

```text
producer -> direct exchange -> queue "bachelor" -> worker/consumer
```

Головна відмінність від `01_hello_world`: тут повідомлення - це не просто текст, а задачі у форматі JSON, і consumer підтверджує їх вручну.

### Producer

```python
channel.exchange_declare(exchange="bachelor exchange", exchange_type="direct")
```

Створюється `direct exchange`. Він маршрутизує повідомлення за точним `routing_key`.

```python
channel.queue_declare(queue="bachelor", durable=True)
```

Створюється черга `bachelor`.

`durable=True` означає, що сама черга не зникне після перезапуску RabbitMQ.

```python
channel.queue_bind(
    exchange="bachelor exchange",
    queue="bachelor",
    routing_key="bachelor",
)
```

Черга `bachelor` прив'язується до exchange `bachelor exchange` з ключем `bachelor`.

Тобто правило маршрутизації таке:

```text
якщо повідомлення прийшло в exchange "bachelor exchange"
і routing_key == "bachelor"
то поклади його в queue "bachelor"
```

Далі створюються задачі:

```python
message = {
    "id": i,
    "payload": f"Date: {datetime.now().isoformat()}",
}
```

Кожна задача перетворюється в JSON і кодується в bytes:

```python
body=json.dumps(message).encode()
```

RabbitMQ передає body як байти, тому словник напряму відправити не можна.

Публікація:

```python
channel.basic_publish(
    exchange="bachelor exchange",
    routing_key="bachelor",
    body=json.dumps(message).encode(),
)
```

### Consumer

```python
channel.queue_declare(queue="bachelor", durable=True)
```

Consumer також оголошує чергу `bachelor`.

```python
message = json.loads(body.decode())
```

Тіло повідомлення приходить як bytes. Його треба:

1. `decode()` - перетворити bytes у string.
2. `json.loads(...)` - перетворити JSON string у Python dict.

```python
time.sleep(0.5)
```

Це імітація довгої роботи. Наче задача реально щось рахує, надсилає email, обробляє файл тощо.

```python
ch.basic_ack(delivery_tag=method.delivery_tag)
```

Це ручне підтвердження. Consumer каже RabbitMQ: "Я обробив цю задачу, можеш видалити її з черги".

```python
channel.basic_qos(prefetch_count=1)
```

Це дуже важливий рядок для worker-ів.

Він означає: не давай одному consumer-у більше ніж одну непідтверджену задачу одночасно.

Якщо запустити кілька consumer-ів, RabbitMQ буде розподіляти задачі між ними більш рівномірно.

Приклад:

```text
task 1 -> consumer A
task 2 -> consumer B
task 3 -> consumer C
task 4 -> consumer A
```

Але consumer A отримає наступну задачу тільки після `basic_ack` для попередньої.

### Як запускати

У першому терміналі:

```bash
python 02_task/consumer.py
```

У другому терміналі:

```bash
python 02_task/producer.py
```

Можна запустити кілька consumer-ів у різних терміналах:

```bash
python 02_task/consumer.py
python 02_task/consumer.py
python 02_task/consumer.py
```

Тоді 100 задач будуть розподілятися між кількома worker-ами.

### Для чого цей приклад

Це модель фонової обробки задач:

- розсилка email;
- генерація звітів;
- обробка зображень;
- імпорт великих CSV;
- запити до зовнішніх API;
- будь-яка робота, яку не хочеться виконувати прямо під час HTTP-запиту.

## 03_Pub-Sub

Файли:

- `03_Pub-Sub/producer.py`
- `03_Pub-Sub/consumer.py`

Це приклад publish/subscribe.

Схема:

```text
producer -> fanout exchange -> всі активні consumers
```

Головна ідея: одне повідомлення отримують усі підписники.

### Producer

```python
channel.exchange_declare(
    exchange="bachelor events message",
    exchange_type="fanout",
)
```

Створюється `fanout exchange`.

`fanout` не дивиться на `routing_key`. Він просто розсилає повідомлення в усі черги, які до нього прив'язані.

Повідомлення:

```python
message = {
    "event": "Test event",
    "message": "Test message",
    "detail": f"Date: {datetime.now().isoformat()}",
}
```

Публікація:

```python
channel.basic_publish(
    exchange="bachelor events message",
    routing_key="",
    body=json.dumps(message).encode(),
)
```

`routing_key=""` тут нормальний, бо для `fanout` routing key не має значення.

### Consumer

```python
q = channel.queue_declare(queue="", exclusive=True)
name_q = q.method.queue
```

Тут consumer створює тимчасову чергу.

`queue=""` означає: RabbitMQ сам згенерує ім'я черги.

`exclusive=True` означає:

- ця черга належить тільки цьому підключенню;
- коли consumer відключиться, черга буде видалена.

Потім ця тимчасова черга підписується на exchange:

```python
channel.queue_bind(exchange="bachelor events message", queue=name_q)
```

Далі consumer слухає свою тимчасову чергу:

```python
channel.basic_consume(queue=name_q, on_message_callback=callback, auto_ack=True)
```

### Як запускати

Запусти кілька consumer-ів у різних терміналах:

```bash
python 03_Pub-Sub/consumer.py
python 03_Pub-Sub/consumer.py
python 03_Pub-Sub/consumer.py
```

Потім запусти producer:

```bash
python 03_Pub-Sub/producer.py
```

Кожен активний consumer отримає одне й те саме повідомлення.

### Різниця між 02_task і 03_Pub-Sub

`02_task` - це черга задач:

```text
одна задача -> один worker
```

Якщо є 3 consumer-и, задача піде тільки одному з них.

`03_Pub-Sub` - це події:

```text
одна подія -> всі підписники
```

Якщо є 3 consumer-и, кожен отримає свою копію події.

Приклад:

```text
02_task:
task 1 -> consumer A
task 2 -> consumer B
task 3 -> consumer C

03_Pub-Sub:
event 1 -> consumer A
event 1 -> consumer B
event 1 -> consumer C
```

## app: RabbitMQ + MongoEngine + CloudAMQP

Файли:

- `app/models.py`
- `app/app.py`
- `app/consumer.py`

Це більш практичний приклад: повідомлення в RabbitMQ містить не всю задачу, а тільки ID документа з MongoDB.

Схема:

```text
producer -> створює Task у MongoDB
producer -> надсилає task.id у RabbitMQ
consumer -> читає task.id
consumer -> знаходить Task у MongoDB
consumer -> позначає Task як completed=True
```

### models.py

```python
connect(
    db="web16",
    host="mongodb+srv://...",
)
```

Це підключення до MongoDB через MongoEngine.

Модель:

```python
class Task(Document):
    completed = BooleanField(default=False)
    consumer = StringField(max_length=150)
```

`Task` - це документ MongoDB.

Поля:

- `completed` - чи виконана задача;
- `consumer` - хто її обробив.

### app.py

Цей файл виступає producer-ом.

Він підключається не до локального RabbitMQ, а до CloudAMQP.

Дані підключення не зберігаються в коді. Вони читаються з `.env` через `python-dotenv`.

За це відповідає `app/config.py`:

```python
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
```

Після цього значення доступні через environment variables:

```python
RABBITMQ_HOST
RABBITMQ_PORT
RABBITMQ_USER
RABBITMQ_PASSWORD
RABBITMQ_VIRTUAL_HOST
```

Далі створюються:

```python
exchange = RABBITMQ_EXCHANGE
queue_name = RABBITMQ_QUEUE
```

Для кожної задачі:

```python
task = Task(consumer="Noname").save()
```

Створюється запис у MongoDB.

Потім у RabbitMQ відправляється тільки ID:

```python
body=str(task.id).encode()
```

Це хороший патерн: у черзі лежить коротке повідомлення, а повні дані зберігаються в базі.

Повідомлення публікується з persistent delivery mode:

```python
properties=pika.BasicProperties(
    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
)
```

Це означає, що RabbitMQ має зберігати повідомлення на диск, якщо черга durable.

Оскільки використовується `direct exchange`, bind має той самий routing key, що й publish:

```python
channel.queue_bind(
    exchange=exchange,
    queue=queue_name,
    routing_key=queue_name,
)
```

### consumer.py

Consumer читає ID задачі:

```python
pk = body.decode()
```

Потім шукає задачу в MongoDB:

```python
task = Task.objects(id=pk, completed=False).first()
```

Тобто він шукає задачу:

- з таким ID;
- яка ще не виконана.

Якщо задача знайдена:

```python
task.update(set__completed=True, set__consumer=consumer)
```

Вона позначається як виконана, а в поле `consumer` записується ім'я worker-а.

Після цього:

```python
ch.basic_ack(delivery_tag=method.delivery_tag)
```

RabbitMQ отримує підтвердження, що повідомлення оброблено.

### Для чого цей приклад

Це вже схоже на реальну архітектуру:

```text
API або producer створює задачу в базі
RabbitMQ повідомляє worker-ам, що є робота
worker бере ID задачі
worker обробляє задачу
worker оновлює статус у базі
```

Так можна будувати:

- системи email-розсилок;
- обробку платежів;
- генерацію документів;
- імпорт даних;
- фонову синхронізацію із зовнішніми сервісами.

## ex_celery

Файли:

- `ex_celery/my_task.py`
- `ex_celery/app.py`

Celery - це високорівнева система для фонових задач. Вона теж використовує брокер повідомлень, але ховає багато ручної роботи.

У RabbitMQ-прикладах ми самі пишемо:

- exchange;
- queue;
- bind;
- publish;
- consume;
- ack.

У Celery ми описуємо Python-функцію як задачу, а Celery сам займається відправкою, виконанням і результатами.

### my_task.py

```python
BROKER_URL = 'redis://localhost:6379/0'
BACKEND_URL = 'redis://localhost:6379/1'
```

Тут Redis використовується у двох ролях:

- broker - черга задач;
- backend - сховище результатів задач.

```python
celery = Celery('tasks', broker=BROKER_URL, backend=BACKEND_URL)
```

Створюється Celery application.

```python
@celery.task(name='Add two numbers')
def add(x, y):
    return x + y
```

Функція `add` реєструється як Celery task.

```python
@celery.task(name='Sub two numbers')
def sub(x, y):
    return x - y
```

Функція `sub` теж стає задачею.

### app.py

```python
result = add.delay(1, 1)
print(result.id)
```

`delay(...)` не виконує функцію прямо тут.

Він створює задачу і відправляє її в broker.

Повертається `AsyncResult`, у якого є `id`. У цьому прикладі ID задач записуються у файл `task_results.json`.

Те саме для `sub`:

```python
result = sub.delay(5, 3)
print(result.id)
```

У цьому прикладі `app.py` тільки ставить задачі в чергу, друкує їхні ID і перезаписує файл `task_results.json`.

Файл спочатку має приблизно такий вигляд:

```json
[
  {
    "name": "add",
    "task_id": "4b77acba-a864-4c5f-8862-3ac2932204ac"
  },
  {
    "name": "sub",
    "task_id": "11374e9f-13ce-42aa-bada-bde67a5e0f96"
  }
]
```

Окремий файл `result.py` читає `task_results.json`, перевіряє стан кожної задачі через Celery backend і знову перезаписує цей самий файл уже з результатами:

```json
[
  {
    "name": "add",
    "task_id": "4b77acba-a864-4c5f-8862-3ac2932204ac",
    "state": "SUCCESS",
    "result": 2
  },
  {
    "name": "sub",
    "task_id": "11374e9f-13ce-42aa-bada-bde67a5e0f96",
    "state": "SUCCESS",
    "result": 2
  }
]
```

Результати зберігаються в Redis backend:

```python
BACKEND_URL = 'redis://localhost:6379/1'
```

Тобто задача лежить у Redis DB `0`, а результат після виконання зберігається в Redis DB `1`.

### Як запускати Celery приклад

Спочатку має бути запущений Redis на `localhost:6379`.

Якщо запускаєш з кореня проєкту, команда для worker-а така:

```bash
uv run celery -A ex_celery.my_task worker --loglevel=INFO --pool solo
```

В іншому терміналі з кореня проєкту треба поставити задачі в чергу:

```bash
uv run python ex_celery/app.py
```

Команда надрукує ID задач, наприклад:

```text
Add task id: 4b77acba-a864-4c5f-8862-3ac2932204ac
Sub task id: 11374e9f-13ce-42aa-bada-bde67a5e0f96
```

Також вона перезапише файл:

```text
ex_celery/task_results.json
```

Щоб пізніше подивитися результати всіх задач із файла:

```bash
uv run python ex_celery/result.py
```

`result.py` прочитає `task_results.json`, підтягне актуальний стан із Redis backend і перезапише файл уже з полями `state` та `result`.

Якщо ти вже перейшов у папку `ex_celery`:

```bash
cd ex_celery
```

Тоді worker запускається так:

```bash
uv run celery -A my_task worker --loglevel=INFO --pool solo
```

А задачі ставляться в чергу так:

```bash
uv run python app.py
```

Результат задачі з цієї ж папки можна подивитися так:

```bash
uv run python result.py
```

`--pool solo` потрібен для Windows. Без нього Celery може падати або некоректно запускати worker через особливості multiprocessing на Windows.

`-A my_task` означає, що Celery має шукати застосунок у файлі `my_task.py`. Якщо запускати з кореня проєкту, треба писати повний шлях до модуля: `ex_celery.my_task`.

`app.py` поставить задачі в Redis, а Celery worker їх виконає.

## Порівняння RabbitMQ і Celery

RabbitMQ + pika - це нижчий рівень.

Ти сам контролюєш:

- назви exchange-ів;
- назви черг;
- routing keys;
- підтвердження повідомлень;
- формат body;
- retry-логіку, якщо вона потрібна.

Celery - це вищий рівень.

Він зручніший, коли треба просто запускати Python-функції у фоні:

- `send_email.delay(...)`;
- `generate_report.delay(...)`;
- `resize_image.delay(...)`.

Celery сам працює з broker-ом і worker-ами, але всередині концепція схожа: задача перетворюється в повідомлення, потрапляє в чергу, worker її забирає і виконує.

## Що треба мати запущеним

Для прикладів `01_hello_world`, `02_task`, `03_Pub-Sub` потрібен RabbitMQ на локальній машині:

```text
localhost:5672
user: guest
password: guest
```

Для `ex_celery` потрібен Redis:

```text
localhost:6379
```

Для `app` потрібні:

- доступ до CloudAMQP;
- доступ до MongoDB Atlas;
- файл `.env` з правильними credentials.

У репозиторії є `.env.example` - це шаблон без секретів.

Локально треба мати `.env` такого формату:

```text
RABBITMQ_HOST=your-cloudamqp-host
RABBITMQ_PORT=5672
RABBITMQ_USER=your-cloudamqp-user
RABBITMQ_PASSWORD=your-cloudamqp-password
RABBITMQ_VIRTUAL_HOST=your-cloudamqp-virtual-host
RABBITMQ_EXCHANGE=Web Service
RABBITMQ_QUEUE=web_campaign
RABBITMQ_CONSUMER_NAME=Krabaton

MONGODB_DB=bachelor
MONGODB_HOST=mongodb+srv://user:password@cluster.example.net/?appName=YourApp
```

Файл `.env` доданий у `.gitignore`, тому його не треба комітити.

## Типові проблеми

### Consumer запущений, але нічого не отримує

Перевір:

- чи запущений RabbitMQ;
- чи producer і consumer використовують однакову назву черги;
- чи producer публікує в правильний exchange;
- чи збігається `routing_key` у `basic_publish` з `routing_key` у `queue_bind`;
- чи consumer слухає саме ту чергу.

### Повідомлення губляться після падіння consumer-а

Якщо використовується:

```python
auto_ack=True
```

RabbitMQ видаляє повідомлення одразу після доставки.

Для задач краще використовувати ручний ack:

```python
ch.basic_ack(delivery_tag=method.delivery_tag)
```

### Durable queue не гарантує збереження повідомлень

`durable=True` зберігає саму чергу.

Щоб повідомлення теж краще переживали перезапуск RabbitMQ, треба публікувати їх як persistent:

```python
properties=pika.BasicProperties(
    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
)
```

У `app/app.py` це вже використовується.

У `02_task/producer.py` черга durable, але повідомлення не persistent.

### У pub/sub повідомлення не приходить старим consumer-ам

У `03_Pub-Sub` черги тимчасові й існують тільки поки consumer підключений.

Якщо producer відправив подію, коли consumer не був запущений, цей consumer її не отримає.

Це нормальна поведінка для такого pub/sub прикладу.

## Коротке резюме

`01_hello_world` показує найпростішу чергу:

```text
один producer -> одна черга -> один consumer
```

`02_task` показує чергу задач:

```text
багато задач -> worker-и розбирають їх по одній
```

`03_Pub-Sub` показує pub/sub:

```text
одна подія -> всі активні підписники
```

`app` показує практичніший сценарій:

```text
RabbitMQ передає ID задачі, MongoDB зберігає стан задачі
```

`ex_celery` показує високорівневий підхід:

```text
Python-функція -> Celery task -> broker -> worker -> result backend
```
