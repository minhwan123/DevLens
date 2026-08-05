from datetime import UTC, datetime
from typing import Any

from devlens.domain.models import RadarSnapshot
from devlens.infrastructure.github.exceptions import GitHubRateLimitExceededError

_ANY_RESET_AT = datetime(2099, 1, 1, tzinfo=UTC)


class FakeGitHubClient:
    """In-memory stand-in for GitHubClientPort, keyed by repo name. No HTTP involved."""

    def __init__(
        self,
        repos: list[dict[str, Any]],
        languages: dict[str, dict[str, int]] | None = None,
        readmes: dict[str, str | None] | None = None,
        contributor_counts: dict[str, int] | None = None,
        commit_counts: dict[str, int] | None = None,
        file_paths: dict[str, list[str]] | None = None,
        manifest_contents: dict[str, dict[str, str]] | None = None,
        fail_repo: str | None = None,
        fail_on_list_repos: bool = False,
    ) -> None:
        self._repos = repos
        self._languages = languages or {}
        self._readmes = readmes or {}
        self._contributor_counts = contributor_counts or {}
        self._commit_counts = commit_counts or {}
        self._file_paths = file_paths or {}
        self._manifest_contents = manifest_contents or {}
        self._fail_repo = fail_repo
        self._fail_on_list_repos = fail_on_list_repos
        self.calls: list[str] = []

    async def list_public_repos(self, username: str) -> list[dict[str, Any]]:
        if self._fail_on_list_repos:
            raise RuntimeError("boom: could not list repositories")
        return self._repos

    async def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        self.calls.append(f"get_languages:{repo}")
        self._maybe_fail(repo)
        return self._languages[repo]

    async def get_readme(self, owner: str, repo: str) -> str | None:
        self.calls.append(f"get_readme:{repo}")
        self._maybe_fail(repo)
        return self._readmes.get(repo)

    async def get_contributors_count(self, owner: str, repo: str) -> int:
        self.calls.append(f"get_contributors_count:{repo}")
        self._maybe_fail(repo)
        return self._contributor_counts[repo]

    async def get_commit_count(self, owner: str, repo: str) -> int:
        self.calls.append(f"get_commit_count:{repo}")
        self._maybe_fail(repo)
        return self._commit_counts[repo]

    async def get_repository_tree(self, owner: str, repo: str, branch: str) -> list[str]:
        self.calls.append(f"get_repository_tree:{repo}")
        self._maybe_fail(repo)
        return self._file_paths.get(repo, [])

    async def get_file_content(self, owner: str, repo: str, path: str) -> str | None:
        self.calls.append(f"get_file_content:{repo}:{path}")
        self._maybe_fail(repo)
        return self._manifest_contents.get(repo, {}).get(path)

    def _maybe_fail(self, repo: str) -> None:
        if repo == self._fail_repo:
            raise GitHubRateLimitExceededError(reset_at=_ANY_RESET_AT)


class FakeSimilarityService:
    """In-memory stand-in for SimilarityPort. No embedding model is loaded."""

    def __init__(self, scores: dict[str, float] | None = None) -> None:
        self._scores = scores or {}
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def rank(self, query_text: str, items: dict[str, str]) -> dict[str, float]:
        self.calls.append((query_text, tuple(items.keys())))
        return {item_id: self._scores.get(item_id, 0.0) for item_id in items}


class FakeCommentaryService:
    """In-memory stand-in for LlmCommentaryPort. No Gemini API call is made."""

    def __init__(self, commentary: str = "fake commentary", fail: bool = False) -> None:
        self._commentary = commentary
        self._fail = fail
        self.prompts: list[str] = []

    async def generate_commentary(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self._fail:
            raise RuntimeError("boom: quota exceeded")
        return self._commentary


class FakeSnapshotRepository:
    """In-memory stand-in for SnapshotRepository. Can simulate a store outage via `fail`."""

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail
        self._snapshots: dict[str, list[RadarSnapshot]] = {}

    async def save(self, username: str, snapshot: RadarSnapshot) -> None:
        if self._fail:
            raise RuntimeError("boom: snapshot store unavailable")
        self._snapshots.setdefault(username, []).append(snapshot)

    async def list_for_username(self, username: str) -> list[RadarSnapshot]:
        if self._fail:
            raise RuntimeError("boom: snapshot store unavailable")
        return list(self._snapshots.get(username, []))
