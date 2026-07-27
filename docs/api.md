# API

Все `/api/v1/*` требуют Telegram или dev авторизацию.

- `GET /api/v1/dashboard` — показатели и остатки.
- `GET /api/v1/fuels` — справочник топлива.
- `PATCH /api/v1/fuels/{id}/price` — цена продажи.
- `POST /api/v1/purchases` — закупка.
- `POST /api/v1/sales` — продажа.
- `POST /api/v1/expenses` — расход.
- `POST /api/v1/collections` — частичная или полная инкассация наличности.
- `GET /api/v1/operations` — неизменяемая история операций.
- `POST /api/v1/operations/{id}/reversal` — компенсирующая отмена.

Финансовые POST-запросы требуют `Idempotency-Key`. Ошибки используют стандартный
FastAPI JSON `{"detail": "..."}`.
