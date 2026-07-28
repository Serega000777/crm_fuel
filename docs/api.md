# API

Все защищённые endpoints требуют Telegram `Authorization: tma ...` либо
`X-Dev-User` только в development.

- `GET /health` — проверка API и базы.
- `GET /api/v1/dashboard` — финансовая сводка владельца.
- `GET /api/v1/fuels` — список топлива.
- `PATCH /api/v1/fuels/{id}/price` — изменение цены.
- `PATCH /api/v1/fuels/{id}/minimum-stock` — порог предупреждения об остатке.
- `POST /api/v1/purchases` — закупка.
- `POST /api/v1/purchases/analyze` — локальный анализ себестоимости.
- `POST /api/v1/sales` — продажа.
- `POST /api/v1/inventory/adjustments` — owner-only инвентаризация фактического остатка.
- `POST /api/v1/expenses` — расход.
- `POST /api/v1/collections` — инкассация.
- `GET /api/v1/operations` — история операций с `limit`, `offset`,
  `operation_type`, `date_from` и `date_to`.
- `POST /api/v1/operations/{id}/reversal` — компенсирующая отмена.
- `GET /api/v1/reports/period` — отчёт владельца за период.
- `GET /api/v1/reports/period.csv` — UTF-8 CSV-выгрузка отчёта.

Параметры отчёта: `date_from=YYYY-MM-DD` и `date_to=YYYY-MM-DD`. Период не может
превышать 366 дней. Показатели строятся из ledger, поэтому reversal автоматически
компенсирует исходные суммы.

Финансовые POST-запросы требуют `Idempotency-Key` длиной 8–100 символов. Ключ
связан с типом и нормализованным payload; изменение содержимого при повторном
ключе возвращает `409`.
