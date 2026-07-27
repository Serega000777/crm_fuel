"""Initial financial and inventory schema."""
from alembic import op

revision = "0001"
down_revision = None

def upgrade():
    bind = op.get_bind()
    from app import models  # noqa: F401
    from app.db import Base
    Base.metadata.create_all(bind)

def downgrade():
    op.drop_table("ledger_entries")
    op.drop_table("operations")
    op.drop_table("fuels")
    op.drop_table("users")

