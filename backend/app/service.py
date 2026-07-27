import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Fuel, LedgerEntry, Operation, OperationType, PaymentMethod, Role, User
from app.schemas import CollectionIn, ExpenseIn, PurchaseIn, ReversalIn, SaleIn


def money(liters: Decimal, unit_price_kopecks: int) -> int:
    return int((liters * Decimal(unit_price_kopecks)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def ensure_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        settings = get_settings()
        if settings.app_env == "production" and user_id != settings.owner_telegram_id:
            raise HTTPException(403, "User is not provisioned")
        role = Role.owner if user_id in {settings.dev_user_id, settings.owner_telegram_id} else Role.operator
        user = User(id=user_id, name="Telegram user", role=role)
        db.add(user)
        db.flush()
    return user


def require_roles(db: Session, user_id: int, *roles: Role) -> User:
    user = ensure_user(db, user_id)
    if user.role not in roles:
        raise HTTPException(403, "Insufficient permissions")
    return user


def request_fingerprint(operation: str, payload: dict) -> str:
    canonical = json.dumps(
        {"operation": operation, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def existing(db: Session, key: str, fingerprint: str) -> Operation | None:
    operation = db.scalar(select(Operation).where(Operation.idempotency_key == key))
    if operation and operation.request_hash != fingerprint:
        raise HTTPException(409, "Idempotency key was already used for another request")
    return operation


def available_balance(db: Session, account: str) -> int:
    return int(
        db.scalar(
            select(func.coalesce(func.sum(LedgerEntry.amount_kopecks), 0)).where(
                LedgerEntry.account == account
            )
        )
        or 0
    )


def transaction_lock(db: Session, namespace: str, value: str) -> None:
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"crm-fuel:{namespace}:{value}"},
        )


def locked_fuel(db: Session, fuel_id: str) -> Fuel | None:
    return db.scalar(
        select(Fuel).where(Fuel.id == fuel_id).with_for_update()
    )


def purchase(db: Session, data: PurchaseIn, key: str, user_id: int) -> Operation:
    transaction_lock(db, "idempotency", key)
    fingerprint = request_fingerprint("purchase", data.model_dump(mode="json"))
    if found := existing(db, key, fingerprint):
        return found
    require_roles(db, user_id, Role.owner)
    fuel = locked_fuel(db, data.fuel_id)
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
                   idempotency_key=key, request_hash=fingerprint, created_by=user_id)
    db.add(op)
    db.flush()
    payment_account = (
        "cash" if data.payment_method == PaymentMethod.cash else "bank"
    )
    transaction_lock(db, "ledger", payment_account)
    db.add(LedgerEntry(operation_id=op.id, account="inventory", amount_kopecks=total))
    db.add(
        LedgerEntry(
            operation_id=op.id, account=payment_account, amount_kopecks=-total
        )
    )
    db.commit()
    return op


def sale(db: Session, data: SaleIn, key: str, user_id: int) -> Operation:
    transaction_lock(db, "idempotency", key)
    fingerprint = request_fingerprint("sale", data.model_dump(mode="json"))
    if found := existing(db, key, fingerprint):
        return found
    require_roles(db, user_id, Role.owner, Role.operator)
    fuel = locked_fuel(db, data.fuel_id)
    if not fuel:
        raise HTTPException(404, "Fuel not found")
    if Decimal(fuel.stock_liters) < data.liters:
        raise HTTPException(409, "Insufficient fuel stock")
    if fuel.sale_price_kopecks <= 0:
        raise HTTPException(409, "Sale price is not configured")
    total = money(data.liters, fuel.sale_price_kopecks)
    cost = money(data.liters, fuel.average_cost_kopecks)
    fuel.stock_liters = Decimal(fuel.stock_liters) - data.liters
    op = Operation(type=OperationType.sale, fuel_id=fuel.id, liters=data.liters,
                   unit_price_kopecks=fuel.sale_price_kopecks, total_kopecks=total,
                   cost_kopecks=cost, payment_method=data.payment_method,
                   idempotency_key=key, request_hash=fingerprint, created_by=user_id)
    db.add(op)
    db.flush()
    account = "cash" if data.payment_method == PaymentMethod.cash else "bank"
    transaction_lock(db, "ledger", account)
    db.add_all([
        LedgerEntry(operation_id=op.id, account=account, amount_kopecks=total),
        LedgerEntry(operation_id=op.id, account="revenue", amount_kopecks=-total),
        LedgerEntry(operation_id=op.id, account="inventory", amount_kopecks=-cost),
        LedgerEntry(operation_id=op.id, account="cogs", amount_kopecks=cost),
    ])
    db.commit()
    return op


def expense(db: Session, data: ExpenseIn, key: str, user_id: int) -> Operation:
    transaction_lock(db, "idempotency", key)
    fingerprint = request_fingerprint("expense", data.model_dump(mode="json"))
    if found := existing(db, key, fingerprint):
        return found
    require_roles(db, user_id, Role.owner, Role.operator)
    account = "cash" if data.payment_method == PaymentMethod.cash else "bank"
    transaction_lock(db, "ledger", account)
    if data.payment_method == PaymentMethod.cash and data.amount_kopecks > available_balance(
        db, account
    ):
        raise HTTPException(409, "Expense exceeds available cash")
    op = Operation(
        type=OperationType.expense,
        total_kopecks=data.amount_kopecks,
        cost_kopecks=0,
        payment_method=data.payment_method,
        description=data.description,
        idempotency_key=key,
        request_hash=fingerprint,
        created_by=user_id,
    )
    db.add(op)
    db.flush()
    db.add_all(
        [
            LedgerEntry(
                operation_id=op.id, account=account, amount_kopecks=-data.amount_kopecks
            ),
            LedgerEntry(
                operation_id=op.id, account="expense", amount_kopecks=data.amount_kopecks
            ),
        ]
    )
    db.commit()
    return op


def collect(db: Session, data: CollectionIn, key: str, user_id: int) -> Operation:
    transaction_lock(db, "idempotency", key)
    fingerprint = request_fingerprint("collection", data.model_dump(mode="json"))
    if found := existing(db, key, fingerprint):
        return found
    require_roles(db, user_id, Role.owner)
    transaction_lock(db, "ledger", "cash")
    available = available_balance(db, "cash")
    amount = data.amount_kopecks if data.amount_kopecks is not None else available
    if amount <= 0 or amount > available:
        raise HTTPException(409, "Collection exceeds available cash")
    op = Operation(
        type=OperationType.collection,
        total_kopecks=amount,
        cost_kopecks=0,
        payment_method=PaymentMethod.cash,
        description=data.description,
        idempotency_key=key,
        request_hash=fingerprint,
        created_by=user_id,
    )
    db.add(op)
    db.flush()
    db.add_all(
        [
            LedgerEntry(operation_id=op.id, account="cash", amount_kopecks=-amount),
            LedgerEntry(operation_id=op.id, account="collection", amount_kopecks=amount),
        ]
    )
    db.commit()
    return op


def reverse(
    db: Session, operation_id: str, data: ReversalIn, key: str, user_id: int
) -> Operation:
    transaction_lock(db, "idempotency", key)
    fingerprint = request_fingerprint(
        "reversal", {"operation_id": operation_id, **data.model_dump(mode="json")}
    )
    if found := existing(db, key, fingerprint):
        return found
    require_roles(db, user_id, Role.owner)
    original = db.scalar(
        select(Operation).where(Operation.id == operation_id).with_for_update()
    )
    if not original:
        raise HTTPException(404, "Operation not found")
    if original.type == OperationType.reversal or original.reversal_of_id:
        raise HTTPException(409, "A reversal cannot be reversed")
    if db.scalar(select(Operation.id).where(Operation.reversal_of_id == original.id)):
        raise HTTPException(409, "Operation is already reversed")

    fuel = locked_fuel(db, original.fuel_id) if original.fuel_id else None
    liters = Decimal(original.liters or 0)
    if original.type == OperationType.purchase and fuel:
        new_stock = Decimal(fuel.stock_liters) - liters
        if new_stock < 0:
            raise HTTPException(409, "Not enough stock to reverse this purchase")
        remaining_value = money(Decimal(fuel.stock_liters), fuel.average_cost_kopecks) - abs(
            original.cost_kopecks
        )
        if remaining_value < 0:
            raise HTTPException(409, "Inventory value prevents reversal")
        fuel.stock_liters = new_stock
        fuel.average_cost_kopecks = (
            0
            if new_stock == 0
            else int(
                (Decimal(remaining_value) / new_stock).quantize(
                    Decimal(1), rounding=ROUND_HALF_UP
                )
            )
        )
    elif original.type == OperationType.sale and fuel:
        new_stock = Decimal(fuel.stock_liters) + liters
        restored_value = money(
            Decimal(fuel.stock_liters), fuel.average_cost_kopecks
        ) + original.cost_kopecks
        fuel.stock_liters = new_stock
        fuel.average_cost_kopecks = int(
            (Decimal(restored_value) / new_stock).quantize(
                Decimal(1), rounding=ROUND_HALF_UP
            )
        )

    op = Operation(
        type=OperationType.reversal,
        fuel_id=original.fuel_id,
        liters=-liters if liters else None,
        unit_price_kopecks=original.unit_price_kopecks,
        total_kopecks=-original.total_kopecks,
        cost_kopecks=-original.cost_kopecks,
        payment_method=original.payment_method,
        description=data.reason,
        reversal_of_id=original.id,
        idempotency_key=key,
        request_hash=fingerprint,
        created_by=user_id,
    )
    db.add(op)
    db.flush()
    entries = list(
        db.scalars(select(LedgerEntry).where(LedgerEntry.operation_id == original.id))
    )
    for account in sorted({entry.account for entry in entries}):
        transaction_lock(db, "ledger", account)
    db.add_all(
        [
            LedgerEntry(
                operation_id=op.id,
                account=entry.account,
                amount_kopecks=-entry.amount_kopecks,
            )
            for entry in entries
        ]
    )
    db.commit()
    return op


def dashboard(db: Session) -> dict:
    fuels = list(db.scalars(select(Fuel).where(Fuel.active.is_(True)).order_by(Fuel.display_order)))
    revenue = db.scalar(select(func.coalesce(func.sum(Operation.total_kopecks), 0)).where(Operation.type == OperationType.sale)) or 0
    cost = db.scalar(select(func.coalesce(func.sum(Operation.cost_kopecks), 0)).where(Operation.type == OperationType.sale)) or 0
    reversed_sales = db.scalar(
        select(func.coalesce(func.sum(Operation.total_kopecks), 0)).where(
            Operation.type == OperationType.reversal,
            Operation.reversal_of_id.in_(
                select(Operation.id).where(Operation.type == OperationType.sale)
            ),
        )
    ) or 0
    reversed_cost = db.scalar(
        select(func.coalesce(func.sum(Operation.cost_kopecks), 0)).where(
            Operation.type == OperationType.reversal,
            Operation.reversal_of_id.in_(
                select(Operation.id).where(Operation.type == OperationType.sale)
            ),
        )
    ) or 0
    expenses = db.scalar(
        select(func.coalesce(func.sum(Operation.total_kopecks), 0)).where(
            Operation.type == OperationType.expense,
            ~Operation.id.in_(
                select(Operation.reversal_of_id).where(
                    Operation.reversal_of_id.is_not(None)
                )
            ),
        )
    ) or 0
    revenue += reversed_sales
    cost += reversed_cost
    cash = db.scalar(select(func.coalesce(func.sum(LedgerEntry.amount_kopecks), 0)).where(LedgerEntry.account == "cash")) or 0
    return {"revenue_kopecks": revenue, "gross_profit_kopecks": revenue - cost,
            "expenses_kopecks": expenses,
            "net_profit_kopecks": revenue - cost - expenses,
            "cash_balance_kopecks": cash,
            "total_stock_liters": sum((Decimal(f.stock_liters) for f in fuels), Decimal(0)),
            "fuels": fuels}
