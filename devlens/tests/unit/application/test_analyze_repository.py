from datetime import UTC, datetime
from typing import Any

from devlens.application.analyze_repository import AnalyzeRepositoryUseCase
from devlens.tests.unit.application.fakes import FakeGitHubClient

_NOW = datetime(2025, 3, 20, tzinfo=UTC)

_FORK_REPO: dict[str, Any] = {
    "name": "old-fork",
    "fork": True,
    "is_template": False,
    "default_branch": "main",
    "created_at": "2020-01-01T00:00:00Z",
    "pushed_at": "2020-01-02T00:00:00Z",
}

_DEVLENS_REPO: dict[str, Any] = {
    "name": "devlens",
    "fork": False,
    "is_template": False,
    "default_branch": "main",
    "created_at": "2025-01-01T00:00:00Z",
    "pushed_at": "2025-03-12T00:00:00Z",
}

_WEAK_REPO: dict[str, Any] = {
    "name": "weak-repo",
    "fork": False,
    "is_template": False,
    "default_branch": "main",
    "created_at": "2020-01-01T00:00:00Z",
    "pushed_at": "2020-01-02T00:00:00Z",
}

_DEVLENS_README = "# DevLens\n\n" + "x" * 500
_DEVLENS_FILE_PATHS = [
    "src/main.py",
    "src/app/manage.py",
    "tests/test_main.py",
    "Dockerfile",
    ".github/workflows/ci.yml",
    "README.md",
]


def _devlens_client(**overrides: Any) -> FakeGitHubClient:
    kwargs: dict[str, Any] = {
        "repos": [_DEVLENS_REPO],
        "languages": {"devlens": {"Python": 8000, "HTML": 2000}},
        "readmes": {"devlens": _DEVLENS_README},
        "contributor_counts": {"devlens": 1},
        "commit_counts": {"devlens": 60},
        "file_paths": {"devlens": _DEVLENS_FILE_PATHS},
    }
    kwargs.update(overrides)
    return FakeGitHubClient(**kwargs)


async def test_fork_is_rejected_without_fetching_repo_details() -> None:
    fake = FakeGitHubClient(repos=[_FORK_REPO])
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    result = await use_case.execute("octocat", "AI Engineer", now=_NOW)

    assert len(result.filter_results) == 1
    assert result.filter_results[0].accepted is False
    assert "Fork" in result.filter_results[0].reason
    assert fake.calls == []


async def test_high_quality_repo_is_accepted_and_populates_profile() -> None:
    fake = _devlens_client()
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    result = await use_case.execute("octocat", "AI Engineer", now=_NOW)

    assert result.partial is False
    assert len(result.filter_results) == 1
    assert result.filter_results[0].accepted is True

    evidence = result.profile.repository_evidences[0]
    assert evidence.repo_name == "devlens"
    assert "Docker" in evidence.tech_stack
    assert evidence.has_tests is True
    assert evidence.has_ci is True
    assert evidence.has_docker is True

    assert result.profile.domains == ["backend", "devops"]
    assert result.profile.project_level == "beginner"
    assert result.profile.career_goal == "AI Engineer"


async def test_non_fork_repo_rejected_by_quality_filter_produces_no_evidence() -> None:
    fake = FakeGitHubClient(
        repos=[_WEAK_REPO],
        languages={"weak-repo": {"Python": 40}},
        readmes={"weak-repo": None},
        contributor_counts={"weak-repo": 1},
        commit_counts={"weak-repo": 1},
        file_paths={"weak-repo": ["main.py"]},
    )
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    result = await use_case.execute("octocat", "AI Engineer", now=_NOW)

    assert len(result.filter_results) == 1
    assert result.filter_results[0].accepted is False
    assert "미달" in result.filter_results[0].reason
    assert result.profile.repository_evidences == []


async def test_mixed_fork_and_quality_repo() -> None:
    fake = _devlens_client(repos=[_FORK_REPO, _DEVLENS_REPO])
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    result = await use_case.execute("octocat", "AI Engineer", now=_NOW)

    assert len(result.filter_results) == 2
    assert result.filter_results[0].accepted is False
    assert result.filter_results[1].accepted is True
    assert [e.repo_name for e in result.profile.repository_evidences] == ["devlens"]


async def test_rate_limit_exceeded_returns_partial_profile() -> None:
    fake = _devlens_client(fail_repo="devlens")
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    result = await use_case.execute("octocat", "AI Engineer", now=_NOW)

    assert result.partial is True
    assert result.filter_results == []
    assert result.profile.repository_evidences == []
    assert result.profile.project_level == "beginner"


async def test_empty_repo_list_returns_empty_profile() -> None:
    fake = FakeGitHubClient(repos=[])
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    result = await use_case.execute("octocat", "AI Engineer", now=_NOW)

    assert result.filter_results == []
    assert result.profile.skills == []
    assert result.profile.domains == []
    assert result.profile.repository_evidences == []


async def test_process_repo_fetches_manifest_when_package_json_present() -> None:
    fake = _devlens_client(
        file_paths={"devlens": [*_DEVLENS_FILE_PATHS, "package.json"]},
        manifest_contents={"devlens": {"package.json": '{"dependencies": {"react": "^18.0.0"}}'}},
    )
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    result = await use_case.execute("octocat", "AI Engineer", now=_NOW)

    assert "get_file_content:devlens:package.json" in fake.calls
    evidence = result.profile.repository_evidences[0]
    assert "React" in evidence.tech_stack


async def test_process_repo_skips_manifest_fetch_when_no_manifest_files_present() -> None:
    fake = _devlens_client()
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    await use_case.execute("octocat", "AI Engineer", now=_NOW)

    assert not any(call.startswith("get_file_content:") for call in fake.calls)


async def test_process_repo_selects_first_match_per_manifest_type_only() -> None:
    fake = _devlens_client(
        file_paths={
            "devlens": [*_DEVLENS_FILE_PATHS, "requirements.txt", "backend/requirements.txt"]
        },
        manifest_contents={"devlens": {"requirements.txt": "fastapi>=0.110\n"}},
    )
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    await use_case.execute("octocat", "AI Engineer", now=_NOW)

    manifest_calls = [call for call in fake.calls if call.startswith("get_file_content:")]
    assert manifest_calls == ["get_file_content:devlens:requirements.txt"]


async def test_process_repo_excludes_manifests_under_node_modules() -> None:
    fake = _devlens_client(
        file_paths={
            "devlens": [*_DEVLENS_FILE_PATHS, "node_modules/foo/package.json", "package.json"]
        },
        manifest_contents={"devlens": {"package.json": '{"dependencies": {"react": "1.0.0"}}'}},
    )
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    await use_case.execute("octocat", "AI Engineer", now=_NOW)

    manifest_calls = [call for call in fake.calls if call.startswith("get_file_content:")]
    assert manifest_calls == ["get_file_content:devlens:package.json"]


async def test_rate_limit_during_manifest_fetch_returns_partial_profile() -> None:
    fake = _devlens_client(
        file_paths={"devlens": [*_DEVLENS_FILE_PATHS, "package.json"]},
        fail_repo="devlens",
    )
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    result = await use_case.execute("octocat", "AI Engineer", now=_NOW)

    assert result.partial is True
    assert result.profile.repository_evidences == []


async def test_skill_proficiency_increases_with_more_supporting_repos() -> None:
    devlens2_repo: dict[str, Any] = {
        "name": "devlens2",
        "fork": False,
        "is_template": False,
        "default_branch": "main",
        "created_at": "2025-01-01T00:00:00Z",
        "pushed_at": "2025-03-12T00:00:00Z",
    }
    fake = FakeGitHubClient(
        repos=[_DEVLENS_REPO, devlens2_repo],
        languages={
            "devlens": {"Python": 8000, "HTML": 2000},
            "devlens2": {"Python": 8000},
        },
        readmes={"devlens": _DEVLENS_README, "devlens2": _DEVLENS_README},
        contributor_counts={"devlens": 1, "devlens2": 1},
        commit_counts={"devlens": 60, "devlens2": 60},
        file_paths={
            "devlens": _DEVLENS_FILE_PATHS,
            "devlens2": ["src/app.py", "tests/test_app.py"],
        },
    )
    use_case = AnalyzeRepositoryUseCase(github_client=fake)

    result = await use_case.execute("octocat", "AI Engineer", now=_NOW)

    assert result.profile.project_level == "intermediate"
    skills_by_name = {skill.skill: skill for skill in result.profile.skills}
    assert skills_by_name["Python"].proficiency == "intermediate"
    assert sorted(skills_by_name["Python"].source_repos) == ["devlens", "devlens2"]
    assert skills_by_name["Docker"].proficiency == "beginner"
