import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException

from app.auth import validate_init_data
from app.config import Settings
from app.db import SessionLocal
from app.models import Role, User


def signed_init_data(token: str, *, auth_date: int | None = None) -> str:
    values = {
        "auth_date": str(auth_date or int(time.time())),
        "query_id": "audit-test",
        "user": json.dumps({"id": 42, "first_name": "Audit"}, separators=(",", ":")),
    }
    check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(
        secret, check_string.encode(), hashlib.sha256
    ).hexdigest()
    return urlencode(values)


def test_telegram_signature_and_freshness():
    token = "123456:test-token"
    assert validate_init_data(signed_init_data(token), token)["id"] == 42
    with pytest.raises(HTTPException) as expired:
        validate_init_data(signed_init_data(token, auth_date=int(time.time()) - 7200), token)
    assert expired.value.status_code == 401
    with pytest.raises(HTTPException):
        validate_init_data("broken-field", token)
    with pytest.raises(HTTPException):
        validate_init_data(signed_init_data(token) + "&user=duplicate", token)


def test_idempotency_key_is_bound_to_request_payload(client):
    headers = {"X-Dev-User": "1", "Idempotency-Key": "same-key-0001"}
    fuel = client.get("/api/v1/fuels", headers=headers).json()[0]
    first = client.post(
        "/api/v1/purchases",
        json={
            "fuel_id": fuel["id"],
            "liters": "10",
            "unit_price_kopecks": 5000,
            "payment_method": "transfer",
        },
        headers=headers,
    )
    assert first.status_code == 200
    conflict = client.post(
        "/api/v1/purchases",
        json={
            "fuel_id": fuel["id"],
            "liters": "11",
            "unit_price_kopecks": 5000,
            "payment_method": "transfer",
        },
        headers=headers,
    )
    assert conflict.status_code == 409


def test_operator_rbac_is_enforced_on_backend(client):
    owner_headers = {"X-Dev-User": "1"}
    fuel = client.get("/api/v1/fuels", headers=owner_headers).json()[0]
    client.post(
        "/api/v1/purchases",
        json={
            "fuel_id": fuel["id"],
            "liters": "10",
            "unit_price_kopecks": 5000,
            "payment_method": "transfer",
        },
        headers={**owner_headers, "Idempotency-Key": "owner-purchase"},
    )
    client.patch(
        f"/api/v1/fuels/{fuel['id']}/price",
        json={"sale_price_kopecks": 6000},
        headers=owner_headers,
    )
    with SessionLocal() as db:
        db.add(User(id=2, name="Operator", role=Role.operator))
        db.commit()
    operator = {"X-Dev-User": "2"}
    assert client.get("/api/v1/dashboard", headers=operator).status_code == 403
    assert (
        client.patch(
            f"/api/v1/fuels/{fuel['id']}/price",
            json={"sale_price_kopecks": 7000},
            headers=operator,
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/purchases",
            json={
                "fuel_id": fuel["id"],
                "liters": "1",
                "unit_price_kopecks": 5000,
                "payment_method": "transfer",
            },
            headers={**operator, "Idempotency-Key": "operator-purchase"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/sales",
            json={"fuel_id": fuel["id"], "liters": "1", "payment_method": "cash"},
            headers={**operator, "Idempotency-Key": "operator-sale-01"},
        ).status_code
        == 200
    )


def test_cash_expense_cannot_overdraw_cash(client):
    response = client.post(
        "/api/v1/expenses",
        json={
            "amount_kopecks": 1,
            "description": "Нет денег",
            "payment_method": "cash",
        },
        headers={"X-Dev-User": "1", "Idempotency-Key": "expense-no-cash"},
    )
    assert response.status_code == 409


def test_security_headers_are_present(client):
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_production_configuration_fails_closed():
    unsafe = Settings(
        app_env="production",
        dev_auth_enabled=True,
        telegram_bot_token="",
        owner_telegram_id=None,
        secret_key="development-only",
        cors_origins="*",
    )
    with pytest.raises(RuntimeError) as error:
        unsafe.validate_runtime()
    assert "DEV_AUTH_ENABLED" in str(error.value)
    safe = Settings(
        app_env="production",
        dev_auth_enabled=False,
        telegram_bot_token="123456:token",
        owner_telegram_id=42,
        secret_key="x" * 32,
        cors_origins="https://crm.example.com",
    )
    safe.validate_runtime()
