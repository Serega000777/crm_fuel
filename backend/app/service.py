from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Fuel, LedgerEntry, Operation, OperationType, PaymentMethod, User
from app.schemas import PurchaseIn, SaleIn


def money(liters: Decimal, unit_price_kopecks: int) -> int:
    return int((liters * Decimal(unit_price_kopecks)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def ensure_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        user = User(id=user_id, name="Владелец", role="owner")
        db.add(user)
        db.flush()
    return user


def existing(db: Session, key: str) -> Operation | None:
    return db.scalar(select(Operation).where(Operation.idempotency_key == key))


def purchase(db: Session, data: PurchaseIn, key: str, user_id: int) -> Operation:
    if found := existing(db, key):
        return found
    ensure_user(db, user_id)
    fuel = db.get(Fuel, data.fuel_id)
    if not fuel:
        raise HTTPException(404, "Fuel not found")
    old_stock = Decimal(fuel.stock_liters)
    new_stock = old_stock + data.liters
    total = money(data.liters, data.unit_price_kopecks)
    weighted = money(old_stock, fuel.average_cost_kopecks) + total
    fuel.stock_liters = new_stock
    fuel.average_cost_kopecks = int((Decimal(weighted) / new_stock).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    fuel.last_purchase_price_kopecks = data.unit_price_kopecks
    op = Operation(type=OperationType.purchase, fuel_id=fuel.id, liters=data.liters,
                   unit_price_kopecks=data.unit_price_kopecks, total_kopecks=total,
                   cost_kopecks=total, payment_method=data.payment_method,
                   idempotency_key=key, created_by=user_id)
    db.add(op)
    db.flush()
    db.add(LedgerEntry(operation_id=op.id, account="inventory", amount_kopecks=total))
    db.add(LedgerEntry(operation_id=op.id, account="cash", amount_kopecks=-total))
    db.commit()
    return op


def sale(db: Session, data: SaleIn, key: str, user_id: int) -> Operation:
    if found := existing(db, key):
        return found
    ensure_user(db, user_id)
    fuel = db.get(Fuel, data.fuel_id)
    if not fuel:
        raise HTTPException(404, "Fuel not found")
    if Decimal(fuel.stock_liters) < data.liters:
        raise HTTPException(409, "Insufficient fuel stock")
    total = money(data.liters, fuel.sale_price_kopecks)
    cost = money(data.liters, fuel.average_cost_kopecks)
    fuel.stock_liters = Decimal(fuel.stock_liters) - data.liters
    op = Operation(type=OperationType.sale, fuel_id=fuel.id, liters=data.liters,
                   unit_price_kopecks=fuel.sale_price_kopecks, total_kopecks=total,
                   cost_kopecks=cost, payment_method=data.payment_method,
                   idempotency_key=key, created_by=user_id)
    db.add(op)
    db.flush()
    account = "cash" if data.payment_method == PaymentMethod.cash else "bank"
    db.add_all([
        LedgerEntry(operation_id=op.id, account=account, amount_kopecks=total),
        LedgerEntry(operation_id=op.id, account="revenue", amount_kopecks=total),
        LedgerEntry(operation_id=op.id, account="inventory", amount_kopecks=-cost),
        LedgerEntry(operation_id=op.id, account="cogs", amount_kopecks=cost),
    ])
    db.commit()
    return op


def dashboard(db: Session) -> dict:
    fuels = list(db.scalars(select(Fuel).where(Fuel.active.is_(True)).order_by(Fuel.display_order)))
    revenue = db.scalar(select(func.coalesce(func.sum(Operation.total_kopecks), 0)).where(Operation.type == OperationType.sale)) or 0
    cost = db.scalar(select(func.coalesce(func.sum(Operation.cost_kopecks), 0)).where(Operation.type == OperationType.sale)) or 0
    cash = db.scalar(select(func.coalesce(func.sum(LedgerEntry.amount_kopecks), 0)).where(LedgerEntry.account == "cash")) or 0
    return {"revenue_kopecks": revenue, "gross_profit_kopecks": revenue - cost,
            "cash_balance_kopecks": cash,
            "total_stock_liters": sum((Decimal(f.stock_liters) for f in fuels), Decimal(0)),
            "fuels": fuels}

