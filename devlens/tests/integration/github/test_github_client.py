import base64
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from devlens.infrastructure.github.client import GitHubClient
from devlens.infrastructure.github.exceptions import GitHubRateLimitExceededError
from devlens.infrastructure.persistence import InMemoryCacheRepository

_BASE_URL = "https://api.github.com"


def _rate_limit_headers(remaining: int = 4999) -> dict[str, str]:
    reset = int((datetime.now(UTC) + timedelta(hours=1)).timestamp())
    return {
        "x-ratelimit-limit": "5000",
        "x-ratelimit-remaining": str(remaining),
        "x-ratelimit-reset": str(reset),
    }


@pytest.fixture
async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(base_url=_BASE_URL) as client:
        yield client


@pytest.fixture
def cache() -> InMemoryCacheRepository:
    return InMemoryCacheRepository()


@respx.mock
async def test_get_languages_returns_language_map(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    route = respx.get(f"{_BASE_URL}/repos/octocat/devlens/languages").mock(
        return_value=httpx.Response(
            200, json={"Python": 1000, "HTML": 50}, headers=_rate_limit_headers()
        )
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    languages = await client.get_languages("octocat", "devlens")

    assert languages == {"Python": 1000, "HTML": 50}
    assert route.call_count == 1


@respx.mock
async def test_repeated_call_is_served_from_cache(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    route = respx.get(f"{_BASE_URL}/repos/octocat/devlens/languages").mock(
        return_value=httpx.Response(200, json={"Python": 1000}, headers=_rate_limit_headers())
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    await client.get_languages("octocat", "devlens")
    await client.get_languages("octocat", "devlens")

    assert route.call_count == 1


@respx.mock
async def test_rate_limit_exceeded_raises(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    respx.get(f"{_BASE_URL}/repos/octocat/devlens/languages").mock(
        return_value=httpx.Response(
            403, json={"message": "rate limited"}, headers=_rate_limit_headers(remaining=0)
        )
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    with pytest.raises(GitHubRateLimitExceededError):
        await client.get_languages("octocat", "devlens")


@respx.mock
async def test_get_readme_returns_none_when_missing(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    headers = _rate_limit_headers()
    respx.get(f"{_BASE_URL}/repos/octocat/devlens/readme").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"}, headers=headers)
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    readme = await client.get_readme("octocat", "devlens")

    assert readme is None


@respx.mock
async def test_get_readme_decodes_base64_content(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    encoded = base64.b64encode(b"# DevLens").decode()
    respx.get(f"{_BASE_URL}/repos/octocat/devlens/readme").mock(
        return_value=httpx.Response(200, json={"content": encoded}, headers=_rate_limit_headers())
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    readme = await client.get_readme("octocat", "devlens")

    assert readme == "# DevLens"


@respx.mock
async def test_get_file_content_returns_none_when_missing(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    respx.get(f"{_BASE_URL}/repos/octocat/devlens/contents/requirements.txt").mock(
        return_value=httpx.Response(
            404, json={"message": "Not Found"}, headers=_rate_limit_headers()
        )
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    content = await client.get_file_content("octocat", "devlens", "requirements.txt")

    assert content is None


@respx.mock
async def test_get_file_content_decodes_base64_content(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    encoded = base64.b64encode(b"fastapi>=0.110").decode()
    respx.get(f"{_BASE_URL}/repos/octocat/devlens/contents/requirements.txt").mock(
        return_value=httpx.Response(
            200,
            json={"content": encoded, "encoding": "base64"},
            headers=_rate_limit_headers(),
        )
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    content = await client.get_file_content("octocat", "devlens", "requirements.txt")

    assert content == "fastapi>=0.110"


@respx.mock
async def test_get_file_content_returns_none_when_too_large(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    respx.get(f"{_BASE_URL}/repos/octocat/devlens/contents/package.json").mock(
        return_value=httpx.Response(
            200,
            json={"encoding": "none", "size": 5_000_000},
            headers=_rate_limit_headers(),
        )
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    content = await client.get_file_content("octocat", "devlens", "package.json")

    assert content is None


@respx.mock
async def test_get_file_content_url_encodes_nested_path(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    encoded = base64.b64encode(b"fastapi>=0.110").decode()
    route = respx.get(
        f"{_BASE_URL}/repos/octocat/devlens/contents/backend/requirements.txt"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"content": encoded, "encoding": "base64"},
            headers=_rate_limit_headers(),
        )
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    content = await client.get_file_content("octocat", "devlens", "backend/requirements.txt")

    assert content == "fastapi>=0.110"
    assert route.call_count == 1


@respx.mock
async def test_list_public_repos_paginates_until_short_page(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    respx.get(f"{_BASE_URL}/users/octocat/repos").mock(
        side_effect=[
            httpx.Response(
                200,
                json=[{"name": f"repo-{i}"} for i in range(100)],
                headers=_rate_limit_headers(),
            ),
            httpx.Response(200, json=[{"name": "repo-100"}], headers=_rate_limit_headers()),
        ]
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    repos = await client.list_public_repos("octocat")

    assert len(repos) == 101


@respx.mock
async def test_get_contributors_count_reads_last_page_from_link_header(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    contributors_url = f"{_BASE_URL}/repos/octocat/devlens/contributors"
    respx.get(contributors_url).mock(
        return_value=httpx.Response(
            200,
            json=[{"login": "octocat"}],
            headers={
                **_rate_limit_headers(),
                "link": (
                    f'<{contributors_url}?per_page=1&page=2>; rel="next", '
                    f'<{contributors_url}?per_page=1&page=7>; rel="last"'
                ),
            },
        )
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    count = await client.get_contributors_count("octocat", "devlens")

    assert count == 7


@respx.mock
async def test_get_contributors_count_without_link_header_counts_body(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    respx.get(f"{_BASE_URL}/repos/octocat/devlens/contributors").mock(
        return_value=httpx.Response(200, json=[{"login": "octocat"}], headers=_rate_limit_headers())
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    count = await client.get_contributors_count("octocat", "devlens")

    assert count == 1


@respx.mock
async def test_get_commit_count_reads_last_page_from_link_header(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    commits_url = f"{_BASE_URL}/repos/octocat/devlens/commits"
    respx.get(commits_url).mock(
        return_value=httpx.Response(
            200,
            json=[{"sha": "abc"}],
            headers={
                **_rate_limit_headers(),
                "link": f'<{commits_url}?per_page=1&page=42>; rel="last"',
            },
        )
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    count = await client.get_commit_count("octocat", "devlens")

    assert count == 42


@respx.mock
async def test_get_repository_tree_returns_only_blob_paths(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    respx.get(f"{_BASE_URL}/repos/octocat/devlens/git/trees/main").mock(
        return_value=httpx.Response(
            200,
            json={
                "tree": [
                    {"path": "src", "type": "tree"},
                    {"path": "src/main.py", "type": "blob"},
                    {"path": "README.md", "type": "blob"},
                ]
            },
            headers=_rate_limit_headers(),
        )
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    paths = await client.get_repository_tree("octocat", "devlens", "main")

    assert paths == ["src/main.py", "README.md"]


@respx.mock
async def test_list_public_repos_returns_empty_list_for_a_user_with_no_repos(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    respx.get(f"{_BASE_URL}/users/octocat/repos").mock(
        return_value=httpx.Response(200, json=[], headers=_rate_limit_headers())
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    repos = await client.list_public_repos("octocat")

    assert repos == []


@respx.mock
async def test_request_sends_bearer_token_when_configured(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    route = respx.get(f"{_BASE_URL}/repos/octocat/devlens/languages").mock(
        return_value=httpx.Response(200, json={"Python": 1000}, headers=_rate_limit_headers())
    )
    client = GitHubClient(cache=cache, http_client=http_client, token="secret-token")

    await client.get_languages("octocat", "devlens")

    assert route.calls.last.request.headers["Authorization"] == "Bearer secret-token"


@respx.mock
async def test_get_contributors_count_with_link_header_missing_last_rel_counts_body(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    contributors_url = f"{_BASE_URL}/repos/octocat/devlens/contributors"
    respx.get(contributors_url).mock(
        return_value=httpx.Response(
            200,
            json=[{"login": "octocat"}],
            headers={
                **_rate_limit_headers(),
                "link": f'<{contributors_url}?per_page=1&page=2>; rel="next"',
            },
        )
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    count = await client.get_contributors_count("octocat", "devlens")

    assert count == 1


@respx.mock
async def test_request_omits_authorization_header_without_a_token(
    http_client: httpx.AsyncClient, cache: InMemoryCacheRepository
) -> None:
    route = respx.get(f"{_BASE_URL}/repos/octocat/devlens/languages").mock(
        return_value=httpx.Response(200, json={"Python": 1000}, headers=_rate_limit_headers())
    )
    client = GitHubClient(cache=cache, http_client=http_client)

    await client.get_languages("octocat", "devlens")

    assert "Authorization" not in route.calls.last.request.headers
