import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException

from app.config import get_settings


def validate_init_data(init_data: str, token: str, max_age: int = 3600) -> dict:
    if not token or not init_data or len(init_data) > 16_384:
        raise HTTPException(401, "Invalid Telegram authorization")
    try:
        pairs = parse_qsl(
            init_data, strict_parsing=True, keep_blank_values=True, max_num_fields=32
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(401, "Malformed Telegram authorization") from exc
    if len({key for key, _ in pairs}) != len(pairs):
        raise HTTPException(401, "Duplicate Telegram authorization fields")
    values = dict(pairs)
    received_hash = values.pop("hash", "")
    check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise HTTPException(401, "Invalid Telegram signature")
    try:
        auth_date = int(values["auth_date"])
        user = json.loads(values["user"])
        user_id = int(user["id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(401, "Malformed Telegram authorization") from exc
    now = int(time.time())
    if auth_date < now - max_age:
        raise HTTPException(401, "Telegram authorization expired")
    if auth_date > now + 60:
        raise HTTPException(401, "Telegram authorization date is in the future")
    user["id"] = user_id
    return user


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
