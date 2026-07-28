import asyncio

from starlette.requests import Request

from app.config import Settings
from app.rate_limit import RedisRateLimiter, request_limit


class FakeRedis:
    def __init__(self):
        self.values: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    async def expire(self, _: str, __: int) -> None:
        return None


def make_request(method: str = "POST") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/api/v1/sales",
            "query_string": b"",
            "headers": [(b"x-dev-user", b"1")],
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


def test_rate_limiter_rejects_request_over_limit():
    settings = Settings(rate_limit_enabled=True, rate_limit_write_per_minute=2)
    limiter = RedisRateLimiter(settings)
    limiter.redis = FakeRedis()  # type: ignore[assignment]

    first = asyncio.run(limiter.check(make_request()))
    second = asyncio.run(limiter.check(make_request()))
    third = asyncio.run(limiter.check(make_request()))

    assert first == (True, 2, 1)
    assert second == (True, 2, 0)
    assert third == (False, 2, 0)


def test_read_and_write_limits_are_independent():
    settings = Settings(
        rate_limit_read_per_minute=100,
        rate_limit_write_per_minute=20,
    )
    assert request_limit(settings, "GET") == 100
    assert request_limit(settings, "POST") == 20


def test_production_requires_rate_limiting():
    settings = Settings(
        app_env="production",
        secret_key="x" * 32,
        telegram_bot_token="token",
        owner_telegram_id=1,
        dev_auth_enabled=False,
        cors_origins="https://crm.example",
        rate_limit_enabled=False,
    )
    try:
        settings.validate_runtime()
    except RuntimeError as error:
        assert "RATE_LIMIT_ENABLED" in str(error)
    else:
        raise AssertionError("Unsafe production settings must fail")
