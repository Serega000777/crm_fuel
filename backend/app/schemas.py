from decimal import Decimal

from pydantic import BaseModel, Field

from app.models import PaymentMethod


class FuelOut(BaseModel):
    id: str
    name: str
    code: str
    stock_liters: Decimal
    sale_price_kopecks: int
    average_cost_kopecks: int
    minimum_stock_liters: Decimal
    color: str
    model_config = {"from_attributes": True}


class PurchaseIn(BaseModel):
    fuel_id: str
    liters: Decimal = Field(gt=0, decimal_places=3)
    unit_price_kopecks: int = Field(gt=0)
    payment_method: PaymentMethod = PaymentMethod.transfer


class SaleIn(BaseModel):
    fuel_id: str
    liters: Decimal = Field(gt=0, decimal_places=3)
    payment_method: PaymentMethod


class PriceIn(BaseModel):
    sale_price_kopecks: int = Field(gt=0)


class OperationOut(BaseModel):
    id: str
    type: str
    total_kopecks: int
    cost_kopecks: int
    liters: Decimal | None
    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    revenue_kopecks: int
    gross_profit_kopecks: int
    cash_balance_kopecks: int
    total_stock_liters: Decimal
    fuels: list[FuelOut]

