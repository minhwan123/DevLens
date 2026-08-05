from abc import ABC, abstractmethod


class CacheRepository(ABC):
    """TTL key-value cache port. Implementations back GitHub API response caching."""

    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int) -> None: ...
