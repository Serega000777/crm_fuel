from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import get_settings
from app.db import Base, engine, get_db
from app.models import Fuel, Operation
from app.schemas import (
    CollectionIn,
    DashboardOut,
    ExpenseIn,
    FuelOut,
    OperationOut,
    PriceIn,
    PurchaseIn,
    ReversalIn,
    SaleIn,
)
from app.service import collect, dashboard, expense, purchase, reverse, sale


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)
    with Session(engine) as db:
        if not db.scalar(select(Fuel.id).limit(1)):
            db.add_all([
                Fuel(name="АИ-92", code="AI92", color="#22C55E", display_order=1),
                Fuel(name="АИ-95", code="AI95", color="#3B82F6", display_order=2),
                Fuel(name="АИ-100", code="AI100", color="#A855F7", display_order=3),
                Fuel(name="ДТ", code="DT", color="#F59E0B", display_order=4),
            ])
            db.commit()
    yield


app = FastAPI(title="CRM Fuel API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().allowed_origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/dashboard", response_model=DashboardOut)
def get_dashboard(_: int = Depends(current_user), db: Session = Depends(get_db)):
    return dashboard(db)


@app.get("/api/v1/fuels", response_model=list[FuelOut])
def get_fuels(_: int = Depends(current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Fuel).order_by(Fuel.display_order)))


@app.patch("/api/v1/fuels/{fuel_id}/price", response_model=FuelOut)
def set_price(fuel_id: str, data: PriceIn, _: int = Depends(current_user), db: Session = Depends(get_db)):
    fuel = db.get(Fuel, fuel_id)
    if not fuel:
        raise HTTPException(404, "Fuel not found")
    fuel.sale_price_kopecks = data.sale_price_kopecks
    db.commit()
    return fuel


@app.post("/api/v1/purchases", response_model=OperationOut)
def create_purchase(data: PurchaseIn, idempotency_key: str = Header(..., alias="Idempotency-Key"),
                    user_id: int = Depends(current_user), db: Session = Depends(get_db)):
    return purchase(db, data, idempotency_key, user_id)


@app.post("/api/v1/sales", response_model=OperationOut)
def create_sale(data: SaleIn, idempotency_key: str = Header(..., alias="Idempotency-Key"),
                user_id: int = Depends(current_user), db: Session = Depends(get_db)):
    return sale(db, data, idempotency_key, user_id)


@app.post("/api/v1/expenses", response_model=OperationOut)
def create_expense(
    data: ExpenseIn,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return expense(db, data, idempotency_key, user_id)


@app.post("/api/v1/collections", response_model=OperationOut)
def create_collection(
    data: CollectionIn,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return collect(db, data, idempotency_key, user_id)


@app.post("/api/v1/operations/{operation_id}/reversal", response_model=OperationOut)
def reverse_operation(
    operation_id: str,
    data: ReversalIn,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return reverse(db, operation_id, data, idempotency_key, user_id)


@app.get("/api/v1/operations", response_model=list[OperationOut])
def list_operations(
    limit: int = 50,
    _: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    safe_limit = max(1, min(limit, 200))
    return list(
        db.scalars(
            select(Operation).order_by(Operation.created_at.desc()).limit(safe_limit)
        )
    )
