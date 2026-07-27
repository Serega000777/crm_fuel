from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import get_settings
from app.db import Base, engine, get_db
from app.models import Fuel, Operation, Role
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
from app.service import (
    collect,
    dashboard,
    expense,
    purchase,
    require_roles,
    reverse,
    sale,
)

IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=100,
        pattern=r"^[A-Za-z0-9._:-]+$",
    ),
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.validate_runtime()
    if settings.database_url.startswith("sqlite"):
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


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if get_settings().app_env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/api/v1/dashboard", response_model=DashboardOut)
def get_dashboard(user_id: int = Depends(current_user), db: Session = Depends(get_db)):
    require_roles(db, user_id, Role.owner)
    return dashboard(db)


@app.get("/api/v1/fuels", response_model=list[FuelOut])
def get_fuels(_: int = Depends(current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Fuel).order_by(Fuel.display_order)))


@app.patch("/api/v1/fuels/{fuel_id}/price", response_model=FuelOut)
def set_price(
    fuel_id: str,
    data: PriceIn,
    user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    require_roles(db, user_id, Role.owner)
    fuel = db.get(Fuel, fuel_id)
    if not fuel:
        raise HTTPException(404, "Fuel not found")
    fuel.sale_price_kopecks = data.sale_price_kopecks
    db.commit()
    return fuel


@app.post("/api/v1/purchases", response_model=OperationOut)
def create_purchase(
    data: PurchaseIn,
    idempotency_key: IdempotencyKey,
    user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return purchase(db, data, idempotency_key, user_id)


@app.post("/api/v1/sales", response_model=OperationOut)
def create_sale(
    data: SaleIn,
    idempotency_key: IdempotencyKey,
    user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return sale(db, data, idempotency_key, user_id)


@app.post("/api/v1/expenses", response_model=OperationOut)
def create_expense(
    data: ExpenseIn,
    idempotency_key: IdempotencyKey,
    user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return expense(db, data, idempotency_key, user_id)


@app.post("/api/v1/collections", response_model=OperationOut)
def create_collection(
    data: CollectionIn,
    idempotency_key: IdempotencyKey,
    user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return collect(db, data, idempotency_key, user_id)


@app.post("/api/v1/operations/{operation_id}/reversal", response_model=OperationOut)
def reverse_operation(
    operation_id: str,
    data: ReversalIn,
    idempotency_key: IdempotencyKey,
    user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    return reverse(db, operation_id, data, idempotency_key, user_id)


@app.get("/api/v1/operations", response_model=list[OperationOut])
def list_operations(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    user_id: int = Depends(current_user),
    db: Session = Depends(get_db),
):
    user = require_roles(db, user_id, Role.owner, Role.operator)
    query = select(Operation)
    if user.role == Role.operator:
        query = query.where(Operation.created_by == user.id)
    return list(
        db.scalars(
            query.order_by(Operation.created_at.desc()).limit(limit)
        )
    )
