from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import LedgerEntry
from app.service import money


def test_money_rounds_half_up():
    assert money(Decimal("10.125"), 6150) == 62269

def test_purchase_sale_and_idempotency(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    purchase = {"fuel_id": fuel["id"], "liters": "100.000", "unit_price_kopecks": 5000, "payment_method": "transfer"}
    result = client.post("/api/v1/purchases", json=purchase, headers={**headers, "Idempotency-Key": "purchase-1"})
    assert result.status_code == 200
    duplicate = client.post("/api/v1/purchases", json=purchase, headers={**headers, "Idempotency-Key": "purchase-1"})
    assert duplicate.json()["id"] == result.json()["id"]
    client.patch(f"/api/v1/fuels/{fuel['id']}/price", json={"sale_price_kopecks": 6500}, headers=headers)
    sold = client.post("/api/v1/sales", json={"fuel_id": fuel["id"], "liters": "10.000", "payment_method": "cash"},
                       headers={**headers, "Idempotency-Key": "sale-0001"})
    assert sold.json()["total_kopecks"] == 65000
    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    assert dashboard["revenue_kopecks"] == 65000
    assert dashboard["gross_profit_kopecks"] == 15000
    assert dashboard["fuels"][0]["stock_liters"] == "90.000"

def test_cannot_sell_more_than_stock(client):
    fuel = client.get("/api/v1/fuels", headers={"X-Dev-User": "1"}).json()[0]
    response = client.post("/api/v1/sales", json={"fuel_id": fuel["id"], "liters": "1", "payment_method": "cash"},
                           headers={"X-Dev-User": "1", "Idempotency-Key": "sale-no-stock"})
    assert response.status_code == 409


def test_expense_collection_and_reversal_preserve_history(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    client.post(
        "/api/v1/purchases",
        json={
            "fuel_id": fuel["id"],
            "liters": "20",
            "unit_price_kopecks": 4000,
            "payment_method": "transfer",
        },
        headers={**headers, "Idempotency-Key": "cash-purchase"},
    )
    client.patch(
        f"/api/v1/fuels/{fuel['id']}/price",
        json={"sale_price_kopecks": 6000},
        headers=headers,
    )
    sale = client.post(
        "/api/v1/sales",
        json={"fuel_id": fuel["id"], "liters": "10", "payment_method": "cash"},
        headers={**headers, "Idempotency-Key": "cash-sale"},
    ).json()
    client.post(
        "/api/v1/expenses",
        json={
            "amount_kopecks": 10000,
            "description": "Доставка",
            "payment_method": "cash",
        },
        headers={**headers, "Idempotency-Key": "expense-1"},
    )
    before = client.get("/api/v1/dashboard", headers=headers).json()
    assert before["cash_balance_kopecks"] == 50000
    assert before["net_profit_kopecks"] == 10000

    reversed_sale = client.post(
        f"/api/v1/operations/{sale['id']}/reversal",
        json={"reason": "Ошибочная продажа"},
        headers={**headers, "Idempotency-Key": "reverse-sale"},
    )
    assert reversed_sale.status_code == 200
    after = client.get("/api/v1/dashboard", headers=headers).json()
    assert after["revenue_kopecks"] == 0
    assert after["cash_balance_kopecks"] == -10000
    assert after["fuels"][0]["stock_liters"] == "20.000"

    collection = client.post(
        "/api/v1/collections",
        json={"amount_kopecks": 1, "description": "Инкассация"},
        headers={**headers, "Idempotency-Key": "collection-no-cash"},
    )
    assert collection.status_code == 409
    history = client.get("/api/v1/operations", headers=headers).json()
    assert len(history) == 4
    assert any(item["reversal_of_id"] == sale["id"] for item in history)


def test_collection_can_take_full_available_cash(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    client.post(
        "/api/v1/purchases",
        json={
            "fuel_id": fuel["id"],
            "liters": "10",
            "unit_price_kopecks": 1000,
            "payment_method": "transfer",
        },
        headers={**headers, "Idempotency-Key": "collect-purchase"},
    )
    client.patch(
        f"/api/v1/fuels/{fuel['id']}/price",
        json={"sale_price_kopecks": 2000},
        headers=headers,
    )
    client.post(
        "/api/v1/sales",
        json={"fuel_id": fuel["id"], "liters": "5", "payment_method": "cash"},
        headers={**headers, "Idempotency-Key": "collect-sale"},
    )
    result = client.post(
        "/api/v1/collections",
        json={"description": "Полная инкассация"},
        headers={**headers, "Idempotency-Key": "collection-full"},
    )
    assert result.status_code == 200
    assert result.json()["total_kopecks"] == 10000
    assert client.get("/api/v1/dashboard", headers=headers).json()[
        "cash_balance_kopecks"
    ] == 0


def test_every_posted_operation_has_balanced_ledger(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    purchase = client.post(
        "/api/v1/purchases",
        json={
            "fuel_id": fuel["id"],
            "liters": "10",
            "unit_price_kopecks": 1000,
            "payment_method": "transfer",
        },
        headers={**headers, "Idempotency-Key": "balanced-purchase"},
    ).json()
    client.patch(
        f"/api/v1/fuels/{fuel['id']}/price",
        json={"sale_price_kopecks": 2000},
        headers=headers,
    )
    sale = client.post(
        "/api/v1/sales",
        json={"fuel_id": fuel["id"], "liters": "5", "payment_method": "cash"},
        headers={**headers, "Idempotency-Key": "balanced-sale"},
    ).json()
    with SessionLocal() as db:
        for operation_id in (purchase["id"], sale["id"]):
            balance = db.scalar(
                select(func.sum(LedgerEntry.amount_kopecks)).where(
                    LedgerEntry.operation_id == operation_id
                )
            )
            assert balance == 0


def test_purchase_analysis_includes_direct_expenses(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    client.patch(
        f"/api/v1/fuels/{fuel['id']}/price",
        json={"sale_price_kopecks": 6500},
        headers=headers,
    )
    payload = {
        "fuel_id": fuel["id"],
        "liters": "100",
        "unit_price_kopecks": 5000,
        "delivery_cost_kopecks": 10000,
        "other_cost_kopecks": 5000,
    }
    analysis = client.post(
        "/api/v1/purchases/analyze", json=payload, headers=headers
    )
    assert analysis.status_code == 200
    result = analysis.json()
    assert result["fuel_cost_kopecks"] == 500000
    assert result["additional_cost_kopecks"] == 15000
    assert result["landed_cost_kopecks"] == 515000
    assert result["batch_cost_per_liter_kopecks"] == 5150
    assert result["projected_average_cost_kopecks"] == 5150
    assert result["projected_margin_per_liter_kopecks"] == 1350
    assert result["projected_margin_basis_points"] == 2077
    assert result["analysis_source"] == "local_rules"
    assert result["profitable"] is True

    purchase = client.post(
        "/api/v1/purchases",
        json={**payload, "payment_method": "transfer"},
        headers={**headers, "Idempotency-Key": "landed-cost-purchase"},
    )
    assert purchase.status_code == 200
    assert purchase.json()["total_kopecks"] == 515000
    assert purchase.json()["additional_cost_kopecks"] == 15000
    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    assert dashboard["fuels"][0]["average_cost_kopecks"] == 5150


def test_purchase_analysis_warns_when_margin_is_negative(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    client.patch(
        f"/api/v1/fuels/{fuel['id']}/price",
        json={"sale_price_kopecks": 5000},
        headers=headers,
    )
    result = client.post(
        "/api/v1/purchases/analyze",
        json={
            "fuel_id": fuel["id"],
            "liters": "10",
            "unit_price_kopecks": 5000,
            "delivery_cost_kopecks": 1000,
            "other_cost_kopecks": 0,
        },
        headers=headers,
    ).json()
    assert result["profitable"] is False
    assert result["projected_margin_per_liter_kopecks"] == -100
    assert "убыточна" in result["advisory"]["summary"].lower()


def test_period_report_and_csv_export(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    client.post(
        "/api/v1/purchases",
        json={
            "fuel_id": fuel["id"],
            "liters": "20",
            "unit_price_kopecks": 4000,
            "payment_method": "transfer",
        },
        headers={**headers, "Idempotency-Key": "report-purchase"},
    )
    client.patch(
        f"/api/v1/fuels/{fuel['id']}/price",
        json={"sale_price_kopecks": 6000},
        headers=headers,
    )
    client.post(
        "/api/v1/sales",
        json={"fuel_id": fuel["id"], "liters": "10", "payment_method": "cash"},
        headers={**headers, "Idempotency-Key": "report-sale"},
    )
    client.post(
        "/api/v1/expenses",
        json={
            "amount_kopecks": 10000,
            "description": "Report expense",
            "payment_method": "cash",
        },
        headers={**headers, "Idempotency-Key": "report-expense"},
    )
    today = datetime.now(UTC).date().isoformat()
    params = {"date_from": today, "date_to": today}
    response = client.get("/api/v1/reports/period", params=params, headers=headers)
    assert response.status_code == 200
    report = response.json()
    assert report["revenue_kopecks"] == 60000
    assert report["cogs_kopecks"] == 40000
    assert report["gross_profit_kopecks"] == 20000
    assert report["expenses_kopecks"] == 10000
    assert report["net_profit_kopecks"] == 10000
    assert report["cash_flow_kopecks"] == 50000
    assert report["purchased_liters"] == "20.000"
    assert report["sold_liters"] == "10.000"
    assert report["operations_count"] == 3
    assert len(report["fuel_details"]) == 1
    fuel_report = report["fuel_details"][0]
    assert fuel_report["fuel_id"] == fuel["id"]
    assert fuel_report["sold_liters"] == "10.000"
    assert fuel_report["revenue_kopecks"] == 60000
    assert fuel_report["cogs_kopecks"] == 40000
    assert fuel_report["gross_profit_kopecks"] == 20000

    exported = client.get("/api/v1/reports/period.csv", params=params, headers=headers)
    assert exported.status_code == 200
    assert exported.content.startswith(b"\xef\xbb\xbfmetric,value")
    assert b"fuel_id,fuel_name,purchased_liters" in exported.content
    assert "attachment;" in exported.headers["content-disposition"]


def test_operation_history_pagination_and_filter(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    client.post(
        "/api/v1/purchases",
        json={
            "fuel_id": fuel["id"],
            "liters": "10",
            "unit_price_kopecks": 4000,
            "payment_method": "transfer",
        },
        headers={**headers, "Idempotency-Key": "history-purchase"},
    )
    client.patch(
        f"/api/v1/fuels/{fuel['id']}/price",
        json={"sale_price_kopecks": 6000},
        headers=headers,
    )
    client.post(
        "/api/v1/sales",
        json={"fuel_id": fuel["id"], "liters": "1", "payment_method": "cash"},
        headers={**headers, "Idempotency-Key": "history-sale"},
    )

    first = client.get(
        "/api/v1/operations", params={"limit": 1, "offset": 0}, headers=headers
    ).json()
    second = client.get(
        "/api/v1/operations", params={"limit": 1, "offset": 1}, headers=headers
    ).json()
    assert len(first) == len(second) == 1
    assert first[0]["id"] != second[0]["id"]
    sales = client.get(
        "/api/v1/operations",
        params={"operation_type": "sale"},
        headers=headers,
    ).json()
    assert len(sales) == 1
    assert sales[0]["type"] == "sale"


def test_inventory_adjustment_is_append_only_and_reversible(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    client.post(
        "/api/v1/purchases",
        json={
            "fuel_id": fuel["id"],
            "liters": "10",
            "unit_price_kopecks": 4000,
            "payment_method": "transfer",
        },
        headers={**headers, "Idempotency-Key": "adjustment-purchase"},
    )
    adjustment = client.post(
        "/api/v1/inventory/adjustments",
        json={
            "fuel_id": fuel["id"],
            "actual_stock_liters": "7",
            "reason": "Physical tank measurement",
        },
        headers={**headers, "Idempotency-Key": "inventory-adjustment"},
    )
    assert adjustment.status_code == 200
    result = adjustment.json()
    assert result["type"] == "adjustment"
    assert result["liters"] == "-3.000"
    assert result["cost_kopecks"] == -12000
    assert (
        client.get("/api/v1/dashboard", headers=headers).json()["fuels"][0][
            "stock_liters"
        ]
        == "7.000"
    )
    with SessionLocal() as db:
        balance = db.scalar(
            select(func.sum(LedgerEntry.amount_kopecks)).where(
                LedgerEntry.operation_id == result["id"]
            )
        )
        assert balance == 0

    reversed_adjustment = client.post(
        f"/api/v1/operations/{result['id']}/reversal",
        json={"reason": "Measurement was incorrect"},
        headers={**headers, "Idempotency-Key": "reverse-adjustment"},
    )
    assert reversed_adjustment.status_code == 200
    assert (
        client.get("/api/v1/dashboard", headers=headers).json()["fuels"][0][
            "stock_liters"
        ]
        == "10.000"
    )


def test_owner_can_configure_minimum_stock(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    response = client.patch(
        f"/api/v1/fuels/{fuel['id']}/minimum-stock",
        json={"minimum_stock_liters": "25.500"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["minimum_stock_liters"] == "25.500"
