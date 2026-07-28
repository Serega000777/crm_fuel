"""Bind idempotency keys to canonical request fingerprints."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade():
    with op.batch_alter_table("operations") as batch_op:
        batch_op.add_column(sa.Column("request_hash", sa.String(64), nullable=True))
    op.execute(
        "UPDATE operations SET request_hash = "
        "lower(hex(randomblob(32)))"
        if op.get_bind().dialect.name == "sqlite"
        else "UPDATE operations SET request_hash = "
        "encode(sha256(convert_to(id, 'UTF8')), 'hex')"
    )
    with op.batch_alter_table("operations") as batch_op:
        batch_op.alter_column("request_hash", nullable=False)


def downgrade():
    with op.batch_alter_table("operations") as batch_op:
        batch_op.drop_column("request_hash")
