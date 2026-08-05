import time
from dataclasses import dataclass

from devlens.infrastructure.persistence.cache_repository import CacheRepository


@dataclass
class _CacheEntry:
    value: str
    expires_at: float


class InMemoryCacheRepository(CacheRepository):
    """Process-local TTL cache. Swap in a PostgreSQL-backed CacheRepository once DB infra exists."""

    def __init__(self) -> None:
        self._store: dict[str, _CacheEntry] = {}

    async def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.monotonic():
            del self._store[key]
            return None
        return entry.value

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._store[key] = _CacheEntry(value=value, expires_at=time.monotonic() + ttl_seconds)
