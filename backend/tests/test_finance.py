from decimal import Decimal

from app.service import money


def test_money_rounds_half_up():
    assert money(Decimal("10.125"), 6150) == 62269

def test_purchase_sale_and_idempotency(client):
    headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    purchase = {"fuel_id": fuel["id"], "liters": "100.000", "unit_price_kopecks": 5000, "payment_method": "transfer"}
    result = client.post("/api/v1/purchases", json=purchase, headers={**headers, "Idempotency-Key": "p-1"})
    assert result.status_code == 200
    duplicate = client.post("/api/v1/purchases", json=purchase, headers={**headers, "Idempotency-Key": "p-1"})
    assert duplicate.json()["id"] == result.json()["id"]
    client.patch(f"/api/v1/fuels/{fuel['id']}/price", json={"sale_price_kopecks": 6500}, headers=headers)
    sold = client.post("/api/v1/sales", json={"fuel_id": fuel["id"], "liters": "10.000", "payment_method": "cash"},
                       headers={**headers, "Idempotency-Key": "s-1"})
    assert sold.json()["total_kopecks"] == 65000
    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    assert dashboard["revenue_kopecks"] == 65000
    assert dashboard["gross_profit_kopecks"] == 15000
    assert dashboard["fuels"][0]["stock_liters"] == "90.000"

def test_cannot_sell_more_than_stock(client):
    fuel = client.get("/api/v1/fuels", headers={"X-Dev-User": "1"}).json()[0]
    response = client.post("/api/v1/sales", json={"fuel_id": fuel["id"], "liters": "1", "payment_method": "cash"},
                           headers={"X-Dev-User": "1", "Idempotency-Key": "s-no-stock"})
    assert response.status_code == 409

