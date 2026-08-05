import hashlib
from typing import Protocol

from devlens.infrastructure.persistence.cache_repository import CacheRepository


class _CommentaryGenerator(Protocol):
    async def generate_commentary(self, prompt: str) -> str: ...


class CachedCommentaryService:
    """Wraps a commentary generator with a TTL cache keyed by the prompt's content hash.

    The prompt is deterministically built from (profile, radar, recommendations, roadmap), so
    hashing it is equivalent to keying on "same profile + career goal" while also correctly
    invalidating if the underlying analysis changes. Repeated report runs for the same
    developer profile reuse the cached commentary instead of re-billing Gemini — the same
    pattern GitHubClient already uses for API responses, applied here to LLM calls.
    """

    def __init__(
        self, inner: _CommentaryGenerator, cache: CacheRepository, ttl_seconds: int
    ) -> None:
        self._inner = inner
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    async def generate_commentary(self, prompt: str) -> str:
        cache_key = f"llm:{hashlib.sha256(prompt.encode()).hexdigest()}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached

        commentary = await self._inner.generate_commentary(prompt)
        await self._cache.set(cache_key, commentary, self._ttl_seconds)
        return commentary
