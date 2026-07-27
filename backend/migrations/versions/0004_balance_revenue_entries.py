"""Correct the sign of legacy revenue ledger entries."""

from alembic import op

revision = "0004"
down_revision = "0003"


def upgrade():
    op.execute(
        "UPDATE ledger_entries SET amount_kopecks = -amount_kopecks "
        "WHERE account = 'revenue' AND amount_kopecks > 0"
    )


def downgrade():
    op.execute(
        "UPDATE ledger_entries SET amount_kopecks = -amount_kopecks "
        "WHERE account = 'revenue' AND amount_kopecks < 0"
    )
