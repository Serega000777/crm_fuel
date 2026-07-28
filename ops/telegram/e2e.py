"""Manual E2E probe for a deployed Telegram bot and Mini App."""

import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request


def fetch_json(url: str, headers: dict[str, str] | None = None) -> dict | list:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(f"Unexpected HTTP status {response.status}: {url}")
        return json.load(response)


def signed_init_data(token: str, user_id: int) -> str:
    values = {
        "auth_date": str(int(time.time())),
        "query_id": "crm-fuel-e2e",
        "user": json.dumps(
            {"id": user_id, "first_name": "CRM Fuel E2E"},
            separators=(",", ":"),
            ensure_ascii=False,
        ),
    }
    check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(
        secret,
        check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    return urllib.parse.urlencode(values)


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    api_url = os.environ["API_URL"].rstrip("/")
    mini_app_url = os.environ["MINI_APP_URL"]
    user_id = int(os.environ["TEST_TELEGRAM_USER_ID"])
    if not api_url.startswith("https://") or not mini_app_url.startswith("https://"):
        raise RuntimeError("API_URL and MINI_APP_URL must use HTTPS")

    telegram = fetch_json(f"https://api.telegram.org/bot{token}/getMe")
    if not isinstance(telegram, dict) or not telegram.get("ok"):
        raise RuntimeError("Telegram getMe failed")
    health = fetch_json(f"{api_url}/health")
    if health != {"status": "ok"}:
        raise RuntimeError(f"Unexpected health response: {health}")
    fuels = fetch_json(
        f"{api_url}/api/v1/fuels",
        {"Authorization": f"tma {signed_init_data(token, user_id)}"},
    )
    if not isinstance(fuels, list) or not fuels:
        raise RuntimeError("Authorized fuel list is empty")
    with urllib.request.urlopen(mini_app_url, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError("Mini App is unavailable")
    print(f"Telegram E2E passed for @{telegram['result']['username']}")


if __name__ == "__main__":
    main()
