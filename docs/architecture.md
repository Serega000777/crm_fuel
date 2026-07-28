# Architecture

React Mini App обращается к REST API FastAPI. API проверяет Telegram initData
или ограниченный dev-auth, выполняет бизнес-правила в транзакции SQLAlchemy и
сохраняет данные в PostgreSQL. Redis зарезервирован для rate limiting и
короткоживущего кэша. UI никогда не определяет финансовый итог.

Модули разделены на transport (`main`, `schemas`), access (`auth`), domain
(`service`) и persistence (`models`, `db`). Это допускает последующую интеграцию
с CRM Cement без копирования финансовых правил.

PostgreSQL `FOR UPDATE` защищает остаток топлива от конкурентного списания.
Transaction-scoped advisory locks сериализуют одинаковые idempotency key и
операции одного ledger-счёта. Каждый запрос получает отдельную SQLAlchemy session
с явным rollback при исключении.
