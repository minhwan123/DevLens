import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from devlens.domain.engines import GithubAnalysisEngine
from devlens.domain.models import (
    DeveloperProfile,
    RepositoryCandidate,
    RepositoryEvidence,
    RepositoryFilterResult,
    RepositoryRawData,
    SkillEvidence,
)
from devlens.domain.policies import ProficiencyPolicy, RepositoryFilterPolicy
from devlens.infrastructure.github.exceptions import GitHubRateLimitExceededError

_MANIFEST_BASENAMES = {"package.json", "requirements.txt", "pyproject.toml"}
_EXCLUDED_PATH_SEGMENTS = {
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "dist",
    "build",
    "site-packages",
}


class GitHubClientPort(Protocol):
    """The subset of GitHubClient this use case depends on, as a structural type.

    Lets tests inject a lightweight fake instead of a real HTTP-backed GitHubClient, and keeps
    this application module decoupled from the concrete infrastructure class.
    """

    async def list_public_repos(self, username: str) -> list[dict[str, Any]]: ...
    async def get_languages(self, owner: str, repo: str) -> dict[str, int]: ...
    async def get_readme(self, owner: str, repo: str) -> str | None: ...
    async def get_contributors_count(self, owner: str, repo: str) -> int: ...
    async def get_commit_count(self, owner: str, repo: str) -> int: ...
    async def get_repository_tree(self, owner: str, repo: str, branch: str) -> list[str]: ...
    async def get_file_content(self, owner: str, repo: str, path: str) -> str | None: ...


def _select_manifest_paths(file_paths: list[str]) -> dict[str, str]:
    """Pick at most one path per known manifest basename, skipping vendored directories."""
    selected: dict[str, str] = {}
    for path in file_paths:
        segments = path.split("/")
        basename = segments[-1].lower()
        if basename not in _MANIFEST_BASENAMES or basename in selected:
            continue
        if any(segment in _EXCLUDED_PATH_SEGMENTS for segment in segments[:-1]):
            continue
        selected[basename] = path
    return selected


@dataclass
class AnalyzeRepositoryResult:
    """Output of AnalyzeRepositoryUseCase: the profile plus a transparent per-repo audit trail."""

    profile: DeveloperProfile
    filter_results: list[RepositoryFilterResult]
    partial: bool = False


class AnalyzeRepositoryUseCase:
    """Builds a DeveloperProfile for a GitHub user: fetch -> filter -> analyze -> aggregate.

    Fork/template repos are rejected without hitting the GitHub API beyond the initial repo
    list, to conserve rate limit. If the rate limit is exhausted mid-scan, the use case stops
    and returns a partial profile from whatever repos it managed to process (graceful
    degradation) instead of failing the whole analysis.
    """

    def __init__(
        self,
        github_client: GitHubClientPort,
        analysis_engine: GithubAnalysisEngine | None = None,
        filter_policy: RepositoryFilterPolicy | None = None,
        proficiency_policy: ProficiencyPolicy | None = None,
    ) -> None:
        self._github = github_client
        self._engine = analysis_engine or GithubAnalysisEngine()
        self._filter_policy = filter_policy or RepositoryFilterPolicy()
        self._proficiency_policy = proficiency_policy or ProficiencyPolicy()

    async def execute(
        self, username: str, career_goal: str, *, now: datetime | None = None
    ) -> AnalyzeRepositoryResult:
        evaluated_at = now or datetime.now(UTC)
        repos = await self._github.list_public_repos(username)

        filter_results: list[RepositoryFilterResult] = []
        evidences: list[RepositoryEvidence] = []
        partial = False

        for repo in repos:
            try:
                filter_result, evidence = await self._process_repo(username, repo, evaluated_at)
            except GitHubRateLimitExceededError:
                partial = True
                break
            filter_results.append(filter_result)
            if evidence is not None:
                evidences.append(evidence)

        profile = self._build_profile(evidences, career_goal)
        return AnalyzeRepositoryResult(
            profile=profile, filter_results=filter_results, partial=partial
        )

    async def _process_repo(
        self, owner: str, repo: dict[str, Any], now: datetime
    ) -> tuple[RepositoryFilterResult, RepositoryEvidence | None]:
        if repo.get("fork", False) or repo.get("is_template", False):
            candidate = _stub_candidate(repo, now=now)
            return self._filter_policy.evaluate(candidate, now=now), None

        raw = await self._fetch_raw_data(owner, repo)
        analysis = self._engine.analyze(raw)
        filter_result = self._filter_policy.evaluate(analysis.candidate, now=now)
        if not filter_result.accepted:
            return filter_result, None
        return filter_result, analysis.to_evidence(filter_result.score)

    async def _fetch_raw_data(self, owner: str, repo: dict[str, Any]) -> RepositoryRawData:
        repo_name = repo["name"]
        languages, readme_text, contributor_count, commit_count, file_paths = await asyncio.gather(
            self._github.get_languages(owner, repo_name),
            self._github.get_readme(owner, repo_name),
            self._github.get_contributors_count(owner, repo_name),
            self._github.get_commit_count(owner, repo_name),
            self._github.get_repository_tree(owner, repo_name, repo["default_branch"]),
        )
        manifest_files = await self._fetch_manifest_files(owner, repo_name, file_paths)
        return RepositoryRawData(
            repo_name=repo_name,
            is_fork=repo.get("fork", False),
            is_template=repo.get("is_template", False),
            created_at=datetime.fromisoformat(repo["created_at"]),
            pushed_at=datetime.fromisoformat(repo["pushed_at"]),
            languages=languages,
            file_paths=file_paths,
            readme_text=readme_text,
            commit_count=commit_count,
            contributor_count=contributor_count,
            manifest_files=manifest_files,
        )

    async def _fetch_manifest_files(
        self, owner: str, repo_name: str, file_paths: list[str]
    ) -> dict[str, str]:
        manifest_paths = _select_manifest_paths(file_paths)
        if not manifest_paths:
            return {}
        contents = await asyncio.gather(
            *(
                self._github.get_file_content(owner, repo_name, path)
                for path in manifest_paths.values()
            )
        )
        return {
            path: content
            for path, content in zip(manifest_paths.values(), contents, strict=True)
            if content is not None
        }

    def _build_profile(
        self, evidences: list[RepositoryEvidence], career_goal: str
    ) -> DeveloperProfile:
        return DeveloperProfile(
            skills=self._build_skills(evidences),
            domains=sorted({tag for evidence in evidences for tag in evidence.domain_tags}),
            career_goal=career_goal,
            project_level=self._proficiency_policy.evaluate(len(evidences)),
            repository_evidences=evidences,
        )

    def _build_skills(self, evidences: list[RepositoryEvidence]) -> list[SkillEvidence]:
        repos_by_skill: dict[str, list[str]] = {}
        for evidence in evidences:
            for tag in evidence.tech_stack:
                repos_by_skill.setdefault(tag, []).append(evidence.repo_name)
        return [
            SkillEvidence(
                skill=skill,
                proficiency=self._proficiency_policy.evaluate(len(source_repos)),
                source_repos=source_repos,
            )
            for skill, source_repos in sorted(repos_by_skill.items())
        ]


def _stub_candidate(repo: dict[str, Any], *, now: datetime) -> RepositoryCandidate:
    """A minimal candidate for repos rejected by rule (fork/template), skipping real signals."""
    return RepositoryCandidate(
        repo_name=repo["name"],
        is_fork=repo.get("fork", False),
        is_template=repo.get("is_template", False),
        commit_count=0,
        contributor_count=0,
        last_activity_at=now,
        readme_length=0,
        readme_has_headings=False,
        code_line_count=0,
        file_extension_count=0,
    )
