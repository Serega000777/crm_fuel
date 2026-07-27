import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException

from app.config import get_settings


def validate_init_data(init_data: str, token: str, max_age: int = 3600) -> dict:
    values = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = values.pop("hash", "")
    check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise HTTPException(401, "Invalid Telegram signature")
    if int(values.get("auth_date", "0")) < time.time() - max_age:
        raise HTTPException(401, "Telegram authorization expired")
    return json.loads(values["user"])


def current_user(
    authorization: str | None = Header(None),
    x_dev_user: int | None = Header(None),
) -> int:
    settings = get_settings()
    if settings.app_env != "production" and settings.dev_auth_enabled and x_dev_user:
        return x_dev_user
    if not authorization or not authorization.startswith("tma "):
        raise HTTPException(401, "Telegram authorization required")
    return int(validate_init_data(authorization[4:], settings.telegram_bot_token)["id"])

