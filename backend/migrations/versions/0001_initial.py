"""Create the initial financial and inventory schema."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None

role = sa.Enum("owner", "operator", "system_admin", name="role")
payment_method = sa.Enum("cash", "card", "transfer", name="paymentmethod")
operation_type = sa.Enum(
    "purchase",
    "sale",
    "expense",
    "collection",
    "adjustment",
    "reversal",
    name="operationtype",
)


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "fuels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("stock_liters", sa.Numeric(18, 3), nullable=False),
        sa.Column("sale_price_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("last_purchase_price_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("average_cost_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("minimum_stock_liters", sa.Numeric(18, 3), nullable=False),
        sa.Column("color", sa.String(20), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("stock_liters >= 0", name="ck_fuels_stock_nonnegative"),
        sa.CheckConstraint(
            "sale_price_kopecks >= 0", name="ck_fuels_sale_price_nonnegative"
        ),
        sa.CheckConstraint(
            "average_cost_kopecks >= 0", name="ck_fuels_average_cost_nonnegative"
        ),
    )
    op.create_table(
        "operations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("type", operation_type, nullable=False),
        sa.Column("fuel_id", sa.String(36), sa.ForeignKey("fuels.id")),
        sa.Column("liters", sa.Numeric(18, 3)),
        sa.Column("unit_price_kopecks", sa.BigInteger()),
        sa.Column("total_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("cost_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("payment_method", payment_method),
        sa.Column("idempotency_key", sa.String(100), nullable=False, unique=True),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_operations_created_at", "operations", ["created_at"])
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "operation_id",
            sa.String(36),
            sa.ForeignKey("operations.id"),
            nullable=False,
        ),
        sa.Column("account", sa.String(30), nullable=False),
        sa.Column("amount_kopecks", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ledger_entries_operation_id", "ledger_entries", ["operation_id"]
    )
    op.create_index("ix_ledger_entries_account", "ledger_entries", ["account"])


def downgrade():
    op.drop_index("ix_ledger_entries_account", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_operation_id", table_name="ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_index("ix_operations_created_at", table_name="operations")
    op.drop_table("operations")
    op.drop_table("fuels")
    op.drop_table("users")
    operation_type.drop(op.get_bind(), checkfirst=True)
    payment_method.drop(op.get_bind(), checkfirst=True)
    role.drop(op.get_bind(), checkfirst=True)
