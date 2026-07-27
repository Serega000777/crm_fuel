"""Add operation descriptions and reversal links."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade():
    op.add_column("operations", sa.Column("description", sa.String(240), nullable=True))
    op.add_column(
        "operations", sa.Column("reversal_of_id", sa.String(36), nullable=True)
    )
    op.create_foreign_key(
        "fk_operations_reversal_of",
        "operations",
        "operations",
        ["reversal_of_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_operations_reversal_of", "operations", ["reversal_of_id"]
    )


def downgrade():
    op.drop_constraint("uq_operations_reversal_of", "operations", type_="unique")
    op.drop_constraint("fk_operations_reversal_of", "operations", type_="foreignkey")
    op.drop_column("operations", "reversal_of_id")
    op.drop_column("operations", "description")
