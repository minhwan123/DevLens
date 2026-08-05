import asyncio

from devlens.infrastructure.llm.cached_commentary_service import CachedCommentaryService
from devlens.infrastructure.persistence.in_memory_cache_repository import InMemoryCacheRepository


class _CountingCommentaryService:
    def __init__(self, commentary: str = "generated commentary") -> None:
        self._commentary = commentary
        self.call_count = 0

    async def generate_commentary(self, prompt: str) -> str:
        self.call_count += 1
        return self._commentary


async def test_repeated_calls_with_the_same_prompt_hit_the_cache() -> None:
    inner = _CountingCommentaryService()
    service = CachedCommentaryService(inner=inner, cache=InMemoryCacheRepository(), ttl_seconds=60)

    first = await service.generate_commentary("same prompt")
    second = await service.generate_commentary("same prompt")

    assert first == second == "generated commentary"
    assert inner.call_count == 1


async def test_different_prompts_are_not_conflated() -> None:
    inner = _CountingCommentaryService()
    service = CachedCommentaryService(inner=inner, cache=InMemoryCacheRepository(), ttl_seconds=60)

    await service.generate_commentary("prompt A")
    await service.generate_commentary("prompt B")

    assert inner.call_count == 2


async def test_expired_cache_entry_calls_the_inner_service_again() -> None:
    inner = _CountingCommentaryService()
    service = CachedCommentaryService(inner=inner, cache=InMemoryCacheRepository(), ttl_seconds=0)

    await service.generate_commentary("same prompt")
    await asyncio.sleep(0.01)
    await service.generate_commentary("same prompt")

    assert inner.call_count == 2
