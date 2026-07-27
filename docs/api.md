# API

Все `/api/v1/*` требуют Telegram или dev авторизацию.

- `GET /api/v1/dashboard` — показатели и остатки.
- `GET /api/v1/fuels` — справочник топлива.
- `PATCH /api/v1/fuels/{id}/price` — цена продажи.
- `POST /api/v1/purchases` — закупка.
- `POST /api/v1/sales` — продажа.

Финансовые POST-запросы требуют `Idempotency-Key`. Ошибки используют стандартный
FastAPI JSON `{"detail": "..."}`.

