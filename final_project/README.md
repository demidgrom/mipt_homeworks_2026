# GigaVibeMiptCode

Консольный Python-чат для общения с LLM

Проект поддерживает:
- обычный чат с моделью
- историю сообщений и ограничение контекста
- настройку через `config.yaml` и переменные окружения
- подстановку файлов через `@::filepath::`
- обработку файла по чанкам через `/file_chunk`
- команды `\q` и `/reset`
- streaming-вывод ответа модели

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Настройка

Создайте файл `config.yaml` по примеру:

```bash
cp config.example.yaml config.yaml
```

Пример конфига для Ollama:

```yaml
api_key: ollama
api_host: http://localhost:11434/v1/
model: gemma3:270m
limit_messages: 20
limit_chars: 4000
temperature: 0.2
system_prompt: You are a math tutor.
stream: true
```

`config.yaml` не нужно коммитить, потому что в нём могут быть секреты. Для этого он добавлен в `.gitignore`

Переменные окружения имеют приоритет над `config.yaml`

Поддерживаемые переменные:

```text
API_KEY
API_HOST
MODEL
LIMIT_MESSAGES
LIMIT_CHARS
TEMPERATURE
STREAM
```

## Запуск Ollama

```bash
ollama pull gemma3:270m
curl http://localhost:11434/api/tags
```

Если Ollama отвечает JSON-ом со списком моделей, можно запускать приложение.

## Запуск программы

```bash
python main.py
```

После запуска появится воод такого типа:

```text
>>> 
```

Здесь можно писать свой вопрос

## Команды

Выход:

```text
\q
```

Сброс истории и очистка экрана:

```text
/reset
```

Прикрепление файла к сообщению:

```text
Что не так с кодом? @::main.py::
```

Обработка файла по чанкам:

```text
/file_chunk
/file_chunk paragraph=3
/file_chunk len=150
/file_chunk paragraph=3 -y
```

Флаг `-y` запускает автоматическую обработку всех чанков без ручного подтверждения.

## Запуск тестов и проверок

Проверка ruff:

```bash
ruff check .
```

Проверка форматирования:

```bash
ruff format --check .
```

Проверка типов:

```bash
mypy .
```

Запуск тестов:

```bash
pytest
```

Запуск тестов с покрытием 51%:

```bash
pytest --cov=src/gigavibemiptcode --cov-report=term-missing --cov-report=html
```

HTML-отчёт покрытия будет создан в папке:

```text
htmlcov/
```

## Структура проекта

```text
src/gigavibemiptcode/
  config.py       # загрузка и проверка конфигурации
  models.py       # общие типы данных
  history.py      # история сообщений и ограничение контекста
  attachments.py  # обработка @::filepath::
  chunking.py     # режим /file_chunk
  llm_client.py   # запросы к OpenAI-compatible API
  cli.py          # консольный интерфейс
  screen.py       # очистка экрана
```

## Запуск тестов и начало работы

```bash
ruff check .
ruff format --check .
mypy .
pytest --cov=src/gigavibemiptcode --cov-report=term-missing --cov-report=html
python main.py
```
