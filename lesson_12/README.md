# Lesson 12 — Тестування в Python

Навчальний проєкт: одні й ті самі сценарії покриті **unittest** і **pytest**. Спочатку проходимо блок `test_unittest_*`, потім — `test_pytest_*`.

## Підготовка

```bash
# з кореня проєкту
uv sync          # або: pip install pytest
```

Активуй віртуальне середовище (`.venv`), якщо ще не активне.

## Структура тестів

```
tests/
  test_unittest_01_ops.py          # unittest, базовий синтаксис
  test_unittest_02_animal.py
  test_unittest_03_get_recipe.py
  test_unittest_04_answer_mock.py
  test_unittest_05_contacts_mock.py
  test_unittest_06_save_data.py

  test_pytest_01_ops.py            # pytest, ті самі сценарії
  test_pytest_02_animal.py
  test_pytest_03_get_recipe.py
  test_pytest_04_answer_mock.py
  test_pytest_05_contacts_mock.py
  test_pytest_06_save_data.py
```

Номер `01…05` — складність. Префікс — фреймворк.

## Як запускати

### Усі тести

```bash
pytest tests/ -v
```

### Лише unittest або лише pytest

```bash
pytest tests/ -k unittest -v
pytest tests/ -k pytest -v
```

### Один файл

```bash
pytest tests/test_unittest_01_ops.py -v
pytest tests/test_pytest_03_get_recipe.py -v
```

### unittest нативно (без pytest)

```bash
python -m unittest tests.test_unittest_01_ops -v
python -m unittest discover -s tests -p "test_unittest_*.py" -v
```

### Короткий вивід

```bash
pytest tests/ -q
```

## Прапори та аргументи команд

У команді `pytest tests/ -k unittest -v` є три частини:

1. **`pytest`** — програма-раннер (запускає тести).
2. **`tests/`** — де шукати тести (папка або конкретний файл).
3. **`-…`** — прапори (опції), що змінюють поведінку.

### pytest

| Прапор | Повна назва | Що робить |
|--------|-------------|-----------|
| `-v` | `--verbose` | Детальний вивід: ім'я кожного тесту + `PASSED` / `FAILED`. Без `-v` — лише крапки або короткий підсумок. |
| `-q` | `--quiet` | Навпаки — мінімум тексту, тільки підсумок (скільки пройшло / впало). |
| `-k unittest` | — | **Фільтр за іменем.** Запускає лише тести, в імені яких є `unittest`. Аналогічно `-k pytest` — лише pytest-файли. Можна `-k "ops and not mock"`. |
| `-x` | `--exitfirst` | Зупинитися після першого падіння (зручно при дебазі). |
| `--tb=short` | — | Короткий traceback при помилці (замість повного стеку). |

**Приклад розбору:**

```bash
pytest tests/test_unittest_01_ops.py -v
#       ↑ файл/папка з тестами          ↑ показати кожен test_* окремо
```

```bash
pytest tests/ -k unittest -v
#       ↑ усі тести в папці   ↑ лише з "unittest" в імені   ↑ детально
```

### unittest (стандартна бібліотека)

| Прапор / аргумент | Що робить |
|-------------------|-----------|
| `-v` | Детальний вивід (`test_add ... ok`). |
| `python -m unittest` | Запуск unittest як модуля Python (рекомендований спосіб). |
| `discover` | Автопошук тестів у папці. |
| `-s tests` | **Start directory** — з якої папки шукати (`tests/`). |
| `-p "test_unittest_*.py"` | **Pattern** — маска імен файлів (лише unittest-файли). |

**Приклад розбору:**

```bash
python -m unittest tests.test_unittest_01_ops -v
#        ↑ модуль unittest    ↑ модуль Python (шлях через крапки)   ↑ детально
```

```bash
python -m unittest discover -s tests -p "test_unittest_*.py" -v
#                 ↑ знайти самому   ↑ папка   ↑ маска файлів          ↑ детально
```

> **Порада:** на занятті для пояснення кожного тесту використовуй `-v`. Для швидкої перевірки «все зелене?» — `-q`.


| # | Файл | Код під тестами | Що перевіряємо |
|---|------|-----------------|----------------|
| **01** | `*_01_ops` | `src/example/ops.py` | Функції `add`, `sub`, `mul`, `div`; ділення на нуль |
| **02** | `*_02_animal` | `src/my_class/main.py` | Класи `Animal`, `Cat`, `Dog`, `CatDog`, `DogCat`; наслідування та MRO |
| **03** | `*_03_get_recipe` | `src/get_recipe/get_recipe.py` | Пошук рецепту в CSV; `mock_open` + `read_data` (без диска) |
| **04** | `*_04_answer_mock` | `src/reduce_sum/answer.py` | Реальна сума (mock `other`) + mock `reduce` (`@patch`) |
| **05** | `*_05_contacts_mock` | `src/method/main.py` | Запис/читання контактів у JSON; `mock_open`; помилки I/O |
| **06** | `*_06_save_data` | `src/save_data/answer.py` | `save_applicant_data()` — запис абітурієнтів у CSV через `mock_open` |

## Різниця між блоками

| Тема | unittest | pytest |
|------|----------|--------|
| Базові перевірки | `TestCase`, `self.assertEqual` | функції + `assert` |
| Підготовка даних | mock I/O (`mock_open`, `read_data`) | те саме |
| Винятки | `self.assertRaises` | `pytest.raises` |
| Дроби | `assertAlmostEqual` | `pytest.approx` |
| Моки | `unittest.mock.patch` | той самий `patch` (працює і в pytest) |

## Приклади сценаріїв

**01 — арифметика**

```python
add(2, 3)   # → 5
div(3, 0)   # → ZeroDivisionError
```

**02 — MRO**

```python
CatDog("Mix", 8).say()   # → "Meow"  (спочатку Cat)
DogCat("Mix", 8).say()   # → "Woof"  (спочатку Dog)
```

**03 — рецепт з CSV**

```python
get_recipe("ingredients.csv", "60b90c1c13067a15887e1ae1")
# → {"id": "...", "name": "Піца", "ingredients": ["томати", "сир", "базилік"]}
```

**04 — сумування через reduce (мок)**

```python
sum_numbers([1, 14, 6, 19, 34, 22])  # → 96
# у тесті reduce підміняється моком, щоб не викликати реальну логіку
```

**05 — контакти в JSON**

```python
write_contacts_to_file("contacts.json", contacts)
read_contacts_from_file("contacts.json")  # → список контактів
# у тесті open/json не чіпають справжній диск — mock_open
```

**06 — абітурієнти в CSV**

```python
save_applicant_data(applicant, "data.csv")
# у тесті open/write не чіпають справжній диск — mock_open
```

## Рекомендований порядок на занятті

1. `test_unittest_01` → … → `test_unittest_06`
2. Пояснити різницю синтаксису unittest vs pytest
3. `test_pytest_01` → … → `test_pytest_06` (порівнювати з unittest-парою)
