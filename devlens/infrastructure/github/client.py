import base64
import json
from typing import Any
from urllib.parse import parse_qs, quote, urlencode, urlparse

import httpx
from pydantic import BaseModel

from devlens.infrastructure.github.exceptions import (
    GitHubRateLimitExceededError,
    GitHubResourceNotFoundError,
)
from devlens.infrastructure.github.rate_limit import RateLimitInfo, parse_rate_limit
from devlens.infrastructure.persistence.cache_repository import CacheRepository

_API_VERSION = "2022-11-28"


class _CachedResponse(BaseModel):
    body: str
    link_header: str | None = None


class GitHubClient:
    """Async wrapper around the GitHub REST API with response caching and rate-limit tracking."""

    def __init__(
        self,
        cache: CacheRepository,
        http_client: httpx.AsyncClient,
        token: str | None = None,
        cache_ttl_seconds: int = 3600,
    ) -> None:
        self._cache = cache
        self._http = http_client
        self._token = token
        self._cache_ttl_seconds = cache_ttl_seconds
        self.last_rate_limit: RateLimitInfo | None = None

    async def list_public_repos(self, username: str) -> list[dict[str, Any]]:
        repos: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = await self._get_json(
                f"/users/{username}/repos",
                params={"type": "owner", "per_page": 100, "page": page},
            )
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return repos

    async def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        return dict(await self._get_json(f"/repos/{owner}/{repo}/languages"))

    async def get_readme(self, owner: str, repo: str) -> str | None:
        try:
            data = await self._get_json(f"/repos/{owner}/{repo}/readme")
        except GitHubResourceNotFoundError:
            return None
        content = data.get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="replace")

    async def get_file_content(self, owner: str, repo: str, path: str) -> str | None:
        try:
            data = await self._get_json(f"/repos/{owner}/{repo}/contents/{quote(path, safe='/')}")
        except GitHubResourceNotFoundError:
            return None
        if not isinstance(data, dict):
            return None
        content = data.get("content")
        if not isinstance(content, str) or data.get("encoding") != "base64":
            return None
        return base64.b64decode(content).decode("utf-8", errors="replace")

    async def get_contributors_count(self, owner: str, repo: str) -> int:
        cached = await self._request(
            f"/repos/{owner}/{repo}/contributors", {"per_page": 1, "anon": "true"}
        )
        return _resolve_count(cached)

    async def get_commit_count(self, owner: str, repo: str) -> int:
        cached = await self._request(f"/repos/{owner}/{repo}/commits", {"per_page": 1})
        return _resolve_count(cached)

    async def get_repository_tree(self, owner: str, repo: str, branch: str) -> list[str]:
        data = await self._get_json(
            f"/repos/{owner}/{repo}/git/trees/{branch}", {"recursive": "1"}
        )
        return [item["path"] for item in data.get("tree", []) if item.get("type") == "blob"]

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        cached = await self._request(path, params)
        return json.loads(cached.body)

    async def _request(self, path: str, params: dict[str, Any] | None = None) -> _CachedResponse:
        cache_key = _build_cache_key(path, params)
        cached_raw = await self._cache.get(cache_key)
        if cached_raw is not None:
            return _CachedResponse.model_validate_json(cached_raw)

        response = await self._http.get(path, params=params, headers=self._headers())
        self.last_rate_limit = parse_rate_limit(response.headers)

        if (
            response.status_code == 403
            and self.last_rate_limit is not None
            and self.last_rate_limit.is_exhausted
        ):
            raise GitHubRateLimitExceededError(self.last_rate_limit.reset_at)
        if response.status_code == 404:
            raise GitHubResourceNotFoundError(path)
        response.raise_for_status()

        result = _CachedResponse(body=response.text, link_header=response.headers.get("link"))
        await self._cache.set(cache_key, result.model_dump_json(), self._cache_ttl_seconds)
        return result

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": _API_VERSION,
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers


def _build_cache_key(path: str, params: dict[str, Any] | None) -> str:
    query = urlencode(sorted((params or {}).items()))
    return f"github:{path}?{query}" if query else f"github:{path}"


def _resolve_count(cached: _CachedResponse) -> int:
    """Derive a total count from a `per_page=1` request: prefer the Link header's last page,
    falling back to counting the (0 or 1 item) body when GitHub omits pagination."""
    last_page = _last_page_from_link_header(cached.link_header)
    if last_page is not None:
        return last_page
    return len(json.loads(cached.body))


def _last_page_from_link_header(link_header: str | None) -> int | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        url_part, _, rel_part = part.strip().partition(";")
        if 'rel="last"' not in rel_part:
            continue
        url = url_part.strip().strip("<>")
        page = parse_qs(urlparse(url).query).get("page")
        if page:
            return int(page[0])
    return None
