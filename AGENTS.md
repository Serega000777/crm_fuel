# AGENTS.md

## Invariants

- Money is integer kopecks. Never use float for money.
- Litres and unit prices at domain boundaries use Decimal.
- Backend is the sole source of calculated totals.
- Purchases, sales, inventory movements and ledger entries are committed in one transaction.
- Every mutating financial endpoint requires an idempotency key.
- Posted financial records are immutable. Corrections use reversal entries.
- Authorization is enforced by backend RBAC.
- Telegram initData must be validated before trusting user identity.
- Never commit secrets or production data.

## Definition of Done

A change includes validation, permissions, audit/idempotency where relevant,
migration, tests, lint/type/build checks, updated documentation and project status.

