import hashlib
import time

from fastapi import Request
from redis.asyncio import Redis

from app.config import Settings


class RedisRateLimiter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.redis: Redis | None = None

    async def connect(self) -> None:
        if not self.settings.rate_limit_enabled:
            return
        self.redis = Redis.from_url(
            self.settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        await self.redis.ping()

    async def close(self) -> None:
        if self.redis is not None:
            await self.redis.aclose()
            self.redis = None

    async def check(self, request: Request) -> tuple[bool, int, int]:
        if not self.settings.rate_limit_enabled or request.url.path == "/health":
            return True, 0, 0
        if self.redis is None:
            raise RuntimeError("Rate limiter is not connected")

        access_class = request_access_class(request.method)
        limit = request_limit(self.settings, request.method)
        window = int(time.time()) // 60
        identity = request.headers.get("X-Telegram-Init-Data")
        if not identity:
            identity = request.headers.get("X-Dev-User")
        if not identity and request.client:
            identity = request.client.host
        digest = hashlib.sha256((identity or "unknown").encode()).hexdigest()[:24]
        key = f"rate:{window}:{digest}:{access_class}"

        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 61)
        remaining = max(0, limit - count)
        return count <= limit, limit, remaining


def request_limit(settings: Settings, method: str) -> int:
    if request_access_class(method) == "read":
        return settings.rate_limit_read_per_minute
    return settings.rate_limit_write_per_minute


def request_access_class(method: str) -> str:
    return "read" if method in {"GET", "HEAD", "OPTIONS"} else "write"
