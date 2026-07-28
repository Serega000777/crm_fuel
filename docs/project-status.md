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

## In progress
Production-readiness review in Draft PR.

## Blocked
Production Telegram token, HTTPS URL and hosting access are intentionally not configured.

## Next tasks
Deployment, production-scale load test, restore rehearsal, Telegram Mini App E2E
and complete employee/RBAC management.

## Known limitations
A production-scale load test and restore rehearsal on the target host remain.

## Owner decisions
Target repository is `Serega000777/crm_fuel`; initial fuels are configurable records.

## Latest branch
`codex/fuel-crm-foundation`

## Latest commit
`c6f2243` — Test PostgreSQL financial concurrency.

## Latest PR
Draft PR #1: https://github.com/Serega000777/crm_fuel/pull/1

## Last successful checks
2026-07-28: Ruff, mypy, 17 pytest tests, Alembic upgrade/downgrade, ESLint,
TypeScript/Vite production build, pip-audit, full npm audit, Compose config and
PostgreSQL 16 multi-session concurrency checks.
