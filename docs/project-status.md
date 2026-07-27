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

## In progress
Production-readiness review in Draft PR.

## Blocked
Production Telegram token, HTTPS URL and hosting access are intentionally not configured.

## Next tasks
Production PostgreSQL concurrency stress test, deployment, restore rehearsal,
Telegram Mini App E2E, period reports, exports and complete employee/RBAC management.

## Known limitations
History currently uses the latest 50 operations. Real PostgreSQL concurrency
stress tests and a restore rehearsal on the target production host remain.

## Owner decisions
Target repository is `Serega000777/crm_fuel`; initial fuels are configurable records.

## Latest branch
`codex/fuel-crm-foundation`

## Latest commit
`c2f099e` — Add rate limiting and database backups.

## Latest PR
Draft PR #1: https://github.com/Serega000777/crm_fuel/pull/1

## Last successful checks
2026-07-27: Ruff, mypy, 17 pytest tests, Alembic upgrade/downgrade, ESLint,
TypeScript/Vite production build, pip-audit, full npm audit and Compose config.
