import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Role(str, enum.Enum):
    owner = "owner"
    operator = "operator"
    system_admin = "system_admin"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    card = "card"
    transfer = "transfer"


class OperationType(str, enum.Enum):
    purchase = "purchase"
    sale = "sale"
    expense = "expense"
    collection = "collection"
    adjustment = "adjustment"
    reversal = "reversal"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.owner)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Fuel(Base):
    __tablename__ = "fuels"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), unique=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    stock_liters: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=Decimal(0))
    sale_price_kopecks: Mapped[int] = mapped_column(BigInteger, default=0)
    last_purchase_price_kopecks: Mapped[int] = mapped_column(BigInteger, default=0)
    average_cost_kopecks: Mapped[int] = mapped_column(BigInteger, default=0)
    minimum_stock_liters: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=Decimal(0))
    color: Mapped[str] = mapped_column(String(20), default="#F59E0B")
    active: Mapped[bool] = mapped_column(default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Operation(Base):
    __tablename__ = "operations"
    __table_args__ = (UniqueConstraint("idempotency_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[OperationType] = mapped_column(Enum(OperationType))
    fuel_id: Mapped[str | None] = mapped_column(ForeignKey("fuels.id"))
    liters: Mapped[Decimal | None] = mapped_column(Numeric(18, 3))
    unit_price_kopecks: Mapped[int | None] = mapped_column(BigInteger)
    total_kopecks: Mapped[int] = mapped_column(BigInteger)
    cost_kopecks: Mapped[int] = mapped_column(BigInteger, default=0)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(Enum(PaymentMethod))
    description: Mapped[str | None] = mapped_column(String(240))
    reversal_of_id: Mapped[str | None] = mapped_column(
        ForeignKey("operations.id"), unique=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(100))
    request_hash: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fuel: Mapped[Fuel | None] = relationship()
    reversal_of: Mapped["Operation | None"] = relationship(
        remote_side="Operation.id", foreign_keys=[reversal_of_id]
    )


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_id: Mapped[str] = mapped_column(ForeignKey("operations.id"))
    account: Mapped[str] = mapped_column(String(30))
    amount_kopecks: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
