from __future__ import annotations

import threading
import time
from typing import Optional

from app.config import get_settings

settings = get_settings()

try:  # pragma: no cover - import branch depends on runtime env
    from redis import Redis
    from redis.exceptions import RedisError
except Exception:  # pragma: no cover - handled by fallback store
    Redis = None  # type: ignore[assignment]
    RedisError = Exception  # type: ignore[assignment,misc]


class InMemorySecurityStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values: dict[str, tuple[str, float]] = {}
        self._counters: dict[str, tuple[int, float]] = {}

    def _prune(self) -> None:
        now = time.time()
        self._values = {
            key: (value, expiry)
            for key, (value, expiry) in self._values.items()
            if expiry > now
        }
        self._counters = {
            key: (count, expiry)
            for key, (count, expiry) in self._counters.items()
            if expiry > now
        }

    def incr_with_window(self, key: str, window_seconds: int) -> tuple[int, int]:
        now = time.time()
        with self._lock:
            self._prune()
            current = self._counters.get(key)
            if current is None:
                expiry = now + window_seconds
                self._counters[key] = (1, expiry)
                return 1, window_seconds

            count, expiry = current
            count += 1
            self._counters[key] = (count, expiry)
            return count, max(1, int(expiry - now))

    def set_with_ttl(self, key: str, value: str, ttl_seconds: int) -> None:
        with self._lock:
            self._prune()
            self._values[key] = (value, time.time() + ttl_seconds)

    def get_value(self, key: str) -> Optional[str]:
        with self._lock:
            self._prune()
            value = self._values.get(key)
            if value is None:
                return None
            return value[0]


class RedisSecurityStore:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    def incr_with_window(self, key: str, window_seconds: int) -> tuple[int, int]:
        try:
            with self.redis_client.pipeline() as pipe:
                pipe.incr(key)
                pipe.ttl(key)
                count, ttl = pipe.execute()
            if ttl in (-1, -2):
                self.redis_client.expire(key, window_seconds)
                ttl = window_seconds
            return int(count), max(1, int(ttl))
        except RedisError:
            return 1, window_seconds

    def set_with_ttl(self, key: str, value: str, ttl_seconds: int) -> None:
        try:
            self.redis_client.setex(key, ttl_seconds, value)
        except RedisError:
            return

    def get_value(self, key: str) -> Optional[str]:
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            return str(value)
        except RedisError:
            return None


_store_cache: Optional[InMemorySecurityStore | RedisSecurityStore] = None
_redis_cache: Optional[Redis] = None


def get_redis_client() -> Optional[Redis]:
    global _redis_cache

    if _redis_cache is not None:
        return _redis_cache

    if Redis is None or not settings.redis_url:
        return None

    try:
        client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        client.ping()
        _redis_cache = client
        return client
    except Exception:
        return None


def is_redis_available() -> bool:
    return get_redis_client() is not None


def get_security_store() -> InMemorySecurityStore | RedisSecurityStore:
    global _store_cache

    if _store_cache is not None:
        return _store_cache

    redis_client = get_redis_client()
    if redis_client is not None:
        _store_cache = RedisSecurityStore(redis_client)
        return _store_cache

    if settings.app_env == "production":
        raise RuntimeError("Redis is required and must be reachable in production")

    _store_cache = InMemorySecurityStore()
    return _store_cache
