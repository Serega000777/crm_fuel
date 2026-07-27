"""Add operation descriptions and reversal links."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade():
    with op.batch_alter_table("operations") as batch_op:
        batch_op.add_column(
            sa.Column("description", sa.String(240), nullable=True)
        )
        batch_op.add_column(
            sa.Column("reversal_of_id", sa.String(36), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_operations_reversal_of",
            "operations",
            ["reversal_of_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_operations_reversal_of", ["reversal_of_id"]
        )


def downgrade():
    with op.batch_alter_table("operations") as batch_op:
        batch_op.drop_constraint("uq_operations_reversal_of", type_="unique")
        batch_op.drop_constraint("fk_operations_reversal_of", type_="foreignkey")
        batch_op.drop_column("reversal_of_id")
        batch_op.drop_column("description")
