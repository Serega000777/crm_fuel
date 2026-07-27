# Project Status

## Current phase
Pre-production security and correctness hardening.
## Completed
Architecture, migrations, Telegram dev/auth, responsive dashboard, fuel prices,
purchases, sales, expenses, collections, reversals, operation history, stock,
weighted cost, ledger, automated tests and Docker.
Completed full code/database/security audit, deterministic migrations, balanced
ledger, request-bound idempotency, concurrency locks and container hardening.
## In progress
Review of audit fixes in Draft PR.
## Blocked
Production Telegram token and URL are intentionally not configured.
## Next tasks
Period reports, exports, employee management and complete RBAC management.
## Known limitations
History currently uses the latest 50 operations. Redis rate limiting, real
PostgreSQL concurrency stress tests and production backup/restore rehearsal remain.
## Owner decisions
Target repository is `Serega000777/crm_fuel`; initial fuels are configurable records.
## Latest branch
`codex/fuel-crm-foundation`
## Latest commit
`8a8126b` — Refactor and secure frontend delivery.
## Latest PR
Draft PR #1: https://github.com/Serega000777/crm_fuel/pull/1
## Last successful checks
2026-07-27: Ruff, mypy, 12 pytest tests, Alembic upgrade/downgrade, ESLint,
TypeScript/Vite production build, pip-audit, full npm audit and Compose config.
