import httpx

from devlens.config.settings import Settings
from devlens.infrastructure.github.client import GitHubClient
from devlens.infrastructure.persistence.cache_repository import CacheRepository


def build_github_client(settings: Settings, cache: CacheRepository) -> GitHubClient:
    http_client = httpx.AsyncClient(base_url=settings.github_api_base_url, timeout=10.0)
    return GitHubClient(
        cache=cache,
        http_client=http_client,
        token=settings.github_token,
        cache_ttl_seconds=settings.github_cache_ttl_seconds,
    )
