import asyncio

from devlens.infrastructure.persistence import InMemoryCacheRepository


async def test_set_then_get_returns_value() -> None:
    cache = InMemoryCacheRepository()

    await cache.set("key", "value", ttl_seconds=60)

    assert await cache.get("key") == "value"


async def test_missing_key_returns_none() -> None:
    cache = InMemoryCacheRepository()

    assert await cache.get("missing") is None


async def test_expired_entry_returns_none() -> None:
    cache = InMemoryCacheRepository()

    await cache.set("key", "value", ttl_seconds=0)
    await asyncio.sleep(0.01)

    assert await cache.get("key") is None
