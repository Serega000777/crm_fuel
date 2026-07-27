# CRM Fuel

Telegram Mini App для учёта закупок, продаж и остатков топлива. Backend является
источником истины: денежные значения хранятся в копейках, литры — в `Decimal`,
а закупка и продажа выполняются атомарно и защищены idempotency key.

## Быстрый старт

```bash
cp .env.example .env
docker compose up --build
```

- Mini App: http://localhost:5173
- API и Swagger: http://localhost:8000/docs
- health check: http://localhost:8000/health

В dev-режиме интерфейс отправляет `X-Dev-User: 1`. В production dev-auth
автоматически запрещён, а Telegram `initData` проверяется на backend.

## Локальная разработка

```bash
cd backend
python -m venv .venv
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

Подробнее: [архитектура](docs/architecture.md), [финансовая модель](docs/financial-model.md)
и [статус проекта](docs/project-status.md).

