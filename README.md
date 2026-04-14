# Payment Processing Service

Сервис для обработки платежей с гарантированной доставкой через паттерн Outbox и брокер сообщений.

**Что делает:**
- Принимает платежи через REST API и создаёт их в статусе `PENDING`
- Гарантирует отправку события в RabbitMQ через Outbox (событие сохраняется в БД атомарно с платежом)
- Consumer обрабатывает платёж через платёжный шлюз (эмуляция), обновляет статус в БД и отправляет webhook на URL, указанный при создании
- Поддерживает идемпотентность: повторный запрос с тем же `Idempotency-Key` возвращает существующий платёж

---

## Стек

| Слой | Технология |
|---|---|
| HTTP API | FastAPI + Uvicorn |
| Брокер сообщений | RabbitMQ (FastStream) |
| БД | PostgreSQL 16 (asyncpg + SQLAlchemy async) |
| Миграции | Alembic |
| Сериализация | orjson, Pydantic v2 |
| Тесты | pytest |
| Контейнеризация | Docker + Docker Compose |

---

## Запуск

### Быстрый старт (Docker Compose)

Поднимает все зависимости (PostgreSQL, RabbitMQ), применяет миграции и запускает API + Consumer:

```bash
docker compose up --build
```

Сервисы после старта:
- **API** — http://localhost:8000
- **Swagger UI** — http://localhost:8000/docs
- **RabbitMQ Management** — http://localhost:15672 (guest / guest)

### Локальный запуск (без Docker)

**1. Зависимости**

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Переменные окружения**

Скопируй `.env.default` в `.env` и при необходимости измени значения:

```bash
cp .env.default .env
```

Содержимое `.env`:

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres

RABBITMQ_USER=guest
RABBITMQ_PASS=guest

API_KEY=secret
OUTBOX_POLL_INTERVAL=2.0

# Для локального запуска (alembic, uvicorn без Docker)
PSQL_DB__DSN=postgresql+asyncpg://postgres:postgres@localhost:5434/postgres
PSQL_DB__MIN_POOL_SIZE=2
PSQL_DB__MAX_POOL_SIZE=5
RABBITMQ__DSN=amqp://guest:guest@localhost:5672/

```

**3. Поднять инфраструктуру**

```bash
docker compose up postgres rabbitmq -d
```

**4. Применить миграции**

```bash
alembic upgrade head
```

**5. Запустить API**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**6. Запустить Consumer** (в отдельном терминале)

```bash
python consumer_main.py
```

### Примеры запросов

**Создать платёж:**

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/payments/' \
  -H 'accept: application/json' \
  -H 'Idempotency-Key: unique-key-001' \
  -H 'X-API-Key: secret' \
  -H 'Content-Type: application/json' \
  -d '{
    "amount": "100.00",
    "currency": "RUB",
    "description": "Оплата заказа #123",
    "webhook_url": "http://api:8000/webhooks/",
    "metadata": {}
  }'
```

**Получить платёж по ID:**

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/payments/{payment_id}' \
  -H 'accept: application/json' \
  -H 'X-API-Key: secret'
```

---

## Тестирование

### Структура тестов

```
tests/
├── conftest.py          # Общие фикстуры (mock-репозитории, sample_payment)
├── unit/
│   └── test_payment_service.py   # Юнит-тесты бизнес-логики PaymentService
└── integration/         # Интеграционные тесты (в разработке)
```

### Юнит-тесты

Юнит-тесты проверяют бизнес-логику `PaymentService` в изоляции — без реальной БД и брокера. Все зависимости заменены на `AsyncMock`.

**Что покрыто:**
- Успешное создание платежа и запись события в Outbox
- Идемпотентность: повторный запрос с тем же `Idempotency-Key` не создаёт новый платёж
- Корректность payload в Outbox-событии (`payment_id`, `webhook_url`)
- Получение платежа по ID
- `PaymentNotFound` при отсутствии платежа

**Запуск:**

```bash
# Все тесты
pytest

# Только юнит-тесты
pytest tests/unit/

# Конкретный тест
pytest tests/unit/test_payment_service.py::TestCreatePayment::test_create_success

# С подробным выводом
pytest -v
```

**Требования для запуска юнит-тестов:** только Python и зависимости из `requirements.txt`. Ни PostgreSQL, ни RabbitMQ не нужны.

### Настройка тестов

Конфигурация pytest (`pytest.ini`):

```ini
[pytest]
pythonpath = .
asyncio_mode = auto
```