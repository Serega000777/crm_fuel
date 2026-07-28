from datetime import date, datetime
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
    delivery_cost_kopecks: int = Field(default=0, ge=0)
    other_cost_kopecks: int = Field(default=0, ge=0)
    payment_method: PaymentMethod = PaymentMethod.transfer


class SaleIn(BaseModel):
    fuel_id: str
    liters: Decimal = Field(gt=0, decimal_places=3)
    payment_method: PaymentMethod


class InventoryAdjustmentIn(BaseModel):
    fuel_id: str
    actual_stock_liters: Decimal = Field(ge=0, decimal_places=3)
    reason: str = Field(min_length=3, max_length=240)


class PriceIn(BaseModel):
    sale_price_kopecks: int = Field(gt=0)


class OperationOut(BaseModel):
    id: str
    type: str
    fuel_id: str | None
    total_kopecks: int
    cost_kopecks: int
    additional_cost_kopecks: int
    liters: Decimal | None
    payment_method: str | None
    description: str | None
    reversal_of_id: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    revenue_kopecks: int
    gross_profit_kopecks: int
    expenses_kopecks: int
    net_profit_kopecks: int
    cash_balance_kopecks: int
    total_stock_liters: Decimal
    fuels: list[FuelOut]


class ExpenseIn(BaseModel):
    amount_kopecks: int = Field(gt=0)
    description: str = Field(min_length=2, max_length=240)
    payment_method: PaymentMethod = PaymentMethod.cash


class CollectionIn(BaseModel):
    amount_kopecks: int | None = Field(default=None, gt=0)
    description: str = Field(default="Инкассация", min_length=2, max_length=240)


class ReversalIn(BaseModel):
    reason: str = Field(min_length=3, max_length=240)


class PurchaseAnalysisIn(BaseModel):
    fuel_id: str
    liters: Decimal = Field(gt=0, decimal_places=3)
    unit_price_kopecks: int = Field(gt=0)
    delivery_cost_kopecks: int = Field(default=0, ge=0)
    other_cost_kopecks: int = Field(default=0, ge=0)


class PurchaseAdvisory(BaseModel):
    summary: str = Field(max_length=500)
    risks: list[str] = Field(max_length=4)
    recommendation: str = Field(max_length=500)


class PurchaseAnalysisOut(BaseModel):
    fuel_cost_kopecks: int
    additional_cost_kopecks: int
    landed_cost_kopecks: int
    batch_cost_per_liter_kopecks: int
    projected_average_cost_kopecks: int
    sale_price_kopecks: int
    projected_margin_per_liter_kopecks: int
    projected_margin_basis_points: int
    profitable: bool
    analysis_source: str
    advisory: PurchaseAdvisory


class PeriodReportOut(BaseModel):
    date_from: date
    date_to: date
    revenue_kopecks: int
    cogs_kopecks: int
    gross_profit_kopecks: int
    expenses_kopecks: int
    net_profit_kopecks: int
    cash_flow_kopecks: int
    purchased_liters: Decimal
    sold_liters: Decimal
    operations_count: int
