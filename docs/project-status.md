# Project Status

## Current phase
Cash operations and immutable financial history.
## Completed
Architecture, migrations, Telegram dev/auth, responsive dashboard, fuel prices,
purchases, sales, expenses, collections, reversals, operation history, stock,
weighted cost, ledger, automated tests and Docker.
## In progress
Validation and publication of the second iteration.
## Blocked
Production Telegram token and URL are intentionally not configured.
## Next tasks
Period reports, exports, employee management and complete RBAC management.
## Known limitations
History currently uses the latest 50 operations; Redis integration and production
rate limiting remain.
## Owner decisions
Target repository is `Serega000777/crm_fuel`; initial fuels are configurable records.
## Latest branch
`codex/fuel-crm-foundation`
## Latest commit
`0cab34f` — branch linked to the initial `main` baseline.
## Latest PR
Draft PR #1: https://github.com/Serega000777/crm_fuel/pull/1
## Last successful checks
2026-07-27: Ruff, mypy, 5 pytest tests, ESLint, TypeScript/Vite production
build and production dependency audit.
