import httpx
import respx

from devlens.config.settings import Settings
from devlens.infrastructure.github.client import GitHubClient
from devlens.infrastructure.github.factory import build_github_client
from devlens.infrastructure.persistence import InMemoryCacheRepository


@respx.mock
async def test_build_github_client_wires_settings_and_cache() -> None:
    settings = Settings(
        github_token="secret",
        github_api_base_url="https://example.invalid",
        github_cache_ttl_seconds=42,
    )
    cache = InMemoryCacheRepository()
    route = respx.get("https://example.invalid/repos/octocat/devlens/languages").mock(
        return_value=httpx.Response(
            200,
            json={"Python": 1000},
            headers={
                "x-ratelimit-limit": "5000",
                "x-ratelimit-remaining": "4999",
                "x-ratelimit-reset": "9999999999",
            },
        )
    )

    client = build_github_client(settings, cache)
    assert isinstance(client, GitHubClient)

    await client.get_languages("octocat", "devlens")

    # Confirms build_github_client actually points the client at settings.github_api_base_url
    # and settings.github_token, rather than just returning any GitHubClient instance.
    assert route.calls.last.request.headers["Authorization"] == "Bearer secret"
    assert await cache.get("github:/repos/octocat/devlens/languages") is not None
