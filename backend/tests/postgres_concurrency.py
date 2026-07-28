"""PostgreSQL-only transaction and locking smoke test, executed by CI."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from fastapi import HTTPException
from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Fuel, LedgerEntry, Operation, OperationType, PaymentMethod, Role, User
from app.schemas import PurchaseIn, SaleIn
from app.service import purchase, sale


def run_sale(
    fuel_id: str,
    liters: str,
    key: str,
    barrier: Barrier,
) -> tuple[str, str | int]:
    with SessionLocal() as db:
        try:
            barrier.wait(timeout=5)
            operation = sale(
                db,
                SaleIn(
                    fuel_id=fuel_id,
                    liters=Decimal(liters),
                    payment_method=PaymentMethod.cash,
                ),
                key,
                1,
            )
            return "ok", operation.id
        except HTTPException as error:
            db.rollback()
            return "error", error.status_code


def main() -> None:
    with SessionLocal() as db:
        if db.get(User, 1) is None:
            db.add(User(id=1, name="Concurrency owner", role=Role.owner))
        fuel = Fuel(
            name="Concurrency fuel",
            code="CONCURRENCY",
            sale_price_kopecks=6500,
        )
        db.add(fuel)
        db.commit()
        fuel_id = fuel.id

    with SessionLocal() as db:
        purchase(
            db,
            PurchaseIn(
                fuel_id=fuel_id,
                liters=Decimal(10),
                unit_price_kopecks=5000,
                payment_method=PaymentMethod.transfer,
            ),
            "pg-initial-purchase",
            1,
        )

    oversell_barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        oversell_results = list(
            pool.map(
                lambda key: run_sale(fuel_id, "7", key, oversell_barrier),
                ("pg-sale-a", "pg-sale-b"),
            )
        )
    assert sorted(status for status, _ in oversell_results) == ["error", "ok"]
    assert ("error", 409) in oversell_results

    with SessionLocal() as db:
        locked_fuel = db.get(Fuel, fuel_id)
        assert locked_fuel is not None
        assert locked_fuel.stock_liters == Decimal("3.000")
        purchase(
            db,
            PurchaseIn(
                fuel_id=fuel_id,
                liters=Decimal(20),
                unit_price_kopecks=5000,
                payment_method=PaymentMethod.transfer,
            ),
            "pg-second-purchase",
            1,
        )

    idempotency_barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        duplicate_results = list(
            pool.map(
                lambda _: run_sale(
                    fuel_id,
                    "5",
                    "pg-duplicate-sale",
                    idempotency_barrier,
                ),
                range(2),
            )
        )
    assert all(status == "ok" for status, _ in duplicate_results)
    assert duplicate_results[0][1] == duplicate_results[1][1]

    with SessionLocal() as db:
        final_fuel = db.get(Fuel, fuel_id)
        assert final_fuel is not None
        assert final_fuel.stock_liters == Decimal("18.000")
        assert (
            db.scalar(
                select(func.count(Operation.id)).where(
                    Operation.idempotency_key == "pg-duplicate-sale"
                )
            )
            == 1
        )
        for operation_id in db.scalars(
            select(Operation.id).where(Operation.type == OperationType.sale)
        ):
            balance = db.scalar(
                select(func.sum(LedgerEntry.amount_kopecks)).where(
                    LedgerEntry.operation_id == operation_id
                )
            )
            assert balance == 0

    print("PostgreSQL concurrency checks passed")


if __name__ == "__main__":
    main()
