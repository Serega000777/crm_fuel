# Testing

Unit test проверяет единое округление. Интеграционные тесты проводят закупку,
продажу, расход, полную инкассацию и reversal, сверяют остаток, кассу, выручку
и прибыль, а также подтверждают сохранение исходной истории. Отдельный тест
запрещает продажу сверх остатка.

Security-набор проверяет Telegram HMAC/freshness, production fail-closed config,
RBAC, привязку idempotency к payload, запрет перерасхода кассы и HTTP headers.
Отдельный инвариант требует нулевую сумму ledger-проводок каждой операции.

Команды: `pytest`, `ruff check .`, `mypy app`, `pip-audit`,
`npm run lint`, `npm run build`, `npm audit`.
