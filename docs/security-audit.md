# Security and Code Audit — 2026-07-27

## Scope

Reviewed backend domain logic, API validation, Telegram authentication, RBAC,
SQLAlchemy transactions, ledger and inventory invariants, Alembic migrations,
frontend money handling, dependencies, Docker images, Nginx and CI.

## Corrected findings

### Critical

1. Fresh migrations depended on current ORM metadata. A new database could
   receive fields from future revisions and then fail on the next migration.
   Migration `0001` is now deterministic; `0002`–`0004` are independently
   upgradeable and downgradeable.
2. Sale ledger entries were not balanced because revenue had the same sign as
   cash income. New entries use the correct opposite sign; `0004` repairs legacy
   entries and a regression test enforces a zero-sum ledger per operation.
3. An idempotency key was not bound to request content. Reusing a key with a
   different payload could return an unrelated operation. `0003` adds a SHA-256
   request fingerprint and conflicts return HTTP 409.

### High

1. Concurrent requests could oversell stock or race cash collection. PostgreSQL
   row locks protect fuel records and transaction-scoped advisory locks serialize
   idempotency keys and ledger accounts.
2. Backend RBAC was incomplete. Purchase, price, dashboard, collection and
   reversal are owner-only; operators can sell, add allowed expenses, view fuels
   and see only their own operation history.
3. Unknown production Telegram users could be auto-provisioned as owners.
   Production now requires `OWNER_TELEGRAM_ID`; unknown users fail closed.
4. Production could start with dev auth, an empty bot token, wildcard CORS or a
   default secret. Startup validation now rejects each unsafe state.
5. Telegram initData parsing could turn malformed input into a server error.
   Parsing is bounded and rejects duplicate fields, missing/invalid JSON, old
   timestamps and future timestamps with HTTP 401.
6. Five high-severity vulnerabilities existed in the ESLint dependency tree.
   The toolchain was upgraded and full npm audit now reports zero vulnerabilities.
   Vulnerable pip and pytest versions were also upgraded.

### Medium

1. Cash expenses could overdraw the cash account. They now require sufficient
   available cash.
2. Sales were possible before a sale price was configured. Backend now rejects
   them with HTTP 409.
3. Frontend converted rubles using floating-point arithmetic. Exact string and
   `BigInt` conversion now produces integer kopecks without binary float drift.
4. API requests had no client timeout. Requests now abort after 15 seconds.
5. Containers ran as root and had writable filesystems. Application containers
   now use unprivileged users, read-only filesystems, tmpfs and
   `no-new-privileges`; Docker contexts exclude development artifacts.
6. Security response headers were absent. API and Nginx now set content type,
   referrer, permissions and framing/CSP controls.

## Verification

- Ruff and mypy pass.
- 12 backend tests pass.
- Telegram signature, malformed payload, freshness, RBAC, idempotency payload,
  cash overdraw, security headers and balanced ledger have regression tests.
- Alembic upgrade to head and downgrade to base pass on a clean database.
- ESLint and TypeScript/Vite production build pass.
- pip-audit and full npm audit report no known vulnerabilities.
- Docker Compose configuration parses successfully.

## Residual risks

- PostgreSQL concurrency is exercised in CI with separate sessions; a larger
  production-scale load test still requires the target host.
- Redis rate limiting and scheduled verified backups are implemented.
- Restore rehearsal, TLS termination, secret rotation and Telegram end-to-end
  checks require the final hosting environment and real bot token.
- Employee management is intentionally deferred by the owner.
