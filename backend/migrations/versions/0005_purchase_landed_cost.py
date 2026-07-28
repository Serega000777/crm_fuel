"""Track direct purchase expenses included in landed cost."""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"


def upgrade():
    with op.batch_alter_table("operations") as batch_op:
        batch_op.add_column(
            sa.Column(
                "additional_cost_kopecks",
                sa.BigInteger(),
                nullable=False,
                server_default="0",
            )
        )


def downgrade():
    with op.batch_alter_table("operations") as batch_op:
        batch_op.drop_column("additional_cost_kopecks")
