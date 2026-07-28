# Project Status

## Current phase
Pre-production security and correctness hardening.

## Completed
Architecture, migrations, Telegram dev/auth, responsive dashboard, fuel prices,
purchases, sales, expenses, collections, reversals, operation history, stock,
weighted cost, ledger, automated tests and Docker.

Completed full code/database/security audit, deterministic migrations, balanced
ledger, request-bound idempotency, concurrency locks and container hardening.

Added local purchase intelligence with delivery/other costs, landed cost per
liter, projected weighted average, margin and rule-based recommendations.

Added Redis-backed production rate limiting, verified scheduled PostgreSQL
backups, an explicit restore procedure and infrastructure checks in CI.

Added a PostgreSQL 16 multi-session CI scenario for overselling protection,
concurrent idempotency and balanced ledgers.

Added owner-only period reports and CSV export based on ledger entries, including
reversal-aware revenue, COGS, expenses, profit, cash flow and fuel volumes.

Added paginated operation history with server-side operation type/date filters
and incremental loading in the Mini App.

Added owner-only append-only inventory reconciliation with balanced ledger entries,
RBAC, idempotency and reversal support.

Added configurable minimum-stock warnings, per-fuel period report details and CSV,
automated CI restore rehearsal, a real-bot Telegram E2E workflow and a read-only
target load-test workflow.

## In progress
Production-readiness review in Draft PR.

## Blocked
Production Telegram token, HTTPS URL and hosting access are intentionally not configured.

## Next tasks
Deployment and execution of the prepared Telegram/load workflows against the
future HTTPS host. Employee management remains intentionally deferred.

## Known limitations
Real-bot Telegram E2E and target load execution require bot/hosting credentials.

## Owner decisions
Target repository is `Serega000777/crm_fuel`; initial fuels are configurable records.

## Latest branch
`codex/fuel-crm-foundation`

## Latest commit
`e71e567` — Restore rehearsal into explicit database.

## Latest PR
Draft PR #1: https://github.com/Serega000777/crm_fuel/pull/1

## Last successful checks
2026-07-28: Ruff, mypy, 21 pytest tests, Alembic upgrade/downgrade, ESLint,
TypeScript/Vite production build, pip-audit, full npm audit, Compose config,
PostgreSQL 16 multi-session concurrency and verified backup/restore rehearsal.
