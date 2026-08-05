from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from devlens.infrastructure.persistence.in_memory_job_repository import InMemoryJobRepository
from devlens.infrastructure.persistence.in_memory_snapshot_repository import (
    InMemorySnapshotRepository,
)
from devlens.interface.api.app import create_app
from devlens.interface.api.dependencies import (
    get_commentary_service,
    get_github_client,
    get_job_repository,
    get_similarity_service,
    get_snapshot_repository,
)
from devlens.tests.unit.application.fakes import (
    FakeCommentaryService,
    FakeGitHubClient,
    FakeSimilarityService,
)

_DEVLENS_REPO: dict[str, Any] = {
    "name": "devlens",
    "fork": False,
    "is_template": False,
    "default_branch": "main",
    "created_at": "2025-01-01T00:00:00Z",
    "pushed_at": "2025-03-12T00:00:00Z",
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


def _make_fake_github_client(**overrides: Any) -> FakeGitHubClient:
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


async def _make_client(
    fake_github: FakeGitHubClient,
    job_repository: InMemoryJobRepository,
    snapshot_repository: InMemorySnapshotRepository | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_github_client] = lambda: fake_github
    app.dependency_overrides[get_similarity_service] = lambda: FakeSimilarityService()
    app.dependency_overrides[get_commentary_service] = lambda: FakeCommentaryService()
    app.dependency_overrides[get_job_repository] = lambda: job_repository
    app.dependency_overrides[get_snapshot_repository] = lambda: (
        snapshot_repository or InMemorySnapshotRepository()
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def job_repository() -> InMemoryJobRepository:
    return InMemoryJobRepository()


@pytest.fixture
async def snapshot_repository() -> InMemorySnapshotRepository:
    return InMemorySnapshotRepository()


@pytest.fixture
async def client(
    job_repository: InMemoryJobRepository,
    snapshot_repository: InMemorySnapshotRepository,
) -> AsyncIterator[httpx.AsyncClient]:
    async for c in _make_client(_make_fake_github_client(), job_repository, snapshot_repository):
        yield c


async def test_health_check(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_analyze_job_completes_and_status_reports_full_result(
    client: httpx.AsyncClient,
) -> None:
    create_response = await client.post(
        "/analyze", json={"username": "octocat", "career_goal": "Backend"}
    )
    assert create_response.status_code == 202
    created = create_response.json()
    assert created["status"] == "pending"
    job_id = created["job_id"]

    status_response = await client.get(f"/analyze/{job_id}/status")
    body = status_response.json()

    assert status_response.status_code == 200
    assert body["status"] == "completed"
    assert body["error"] is None
    evidences = body["result"]["profile"]["repository_evidences"]
    assert [e["repo_name"] for e in evidences] == ["devlens"]
    assert body["result"]["radar"]["programming"] >= 0
    assert isinstance(body["result"]["recommendations"], list)
    assert isinstance(body["result"]["suggestions"], list)
    assert len(body["result"]["role_fit"]) == 3
    assert len(body["result"]["history"]) == 1
    assert isinstance(body["result"]["roadmap"], list)
    assert body["result"]["ai_commentary"] == "fake commentary"
    assert isinstance(body["result"]["strengths"], list)
    assert isinstance(body["result"]["growth_areas"], list)


async def test_reanalyzing_the_same_username_accumulates_history(
    client: httpx.AsyncClient,
) -> None:
    first_create = await client.post(
        "/analyze", json={"username": "octocat", "career_goal": "Backend"}
    )
    first_status = await client.get(f"/analyze/{first_create.json()['job_id']}/status")
    assert len(first_status.json()["result"]["history"]) == 1

    second_create = await client.post(
        "/analyze", json={"username": "octocat", "career_goal": "Backend"}
    )
    second_status = await client.get(f"/analyze/{second_create.json()['job_id']}/status")

    assert len(second_status.json()["result"]["history"]) == 2


async def test_report_pdf_is_downloadable_once_the_job_completes(
    client: httpx.AsyncClient,
) -> None:
    create_response = await client.post(
        "/analyze", json={"username": "octocat", "career_goal": "Backend"}
    )
    job_id = create_response.json()["job_id"]

    response = await client.get(f"/analyze/{job_id}/report.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


async def test_report_pdf_for_unknown_job_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/analyze/does-not-exist/report.pdf")

    assert response.status_code == 404


async def test_report_pdf_before_completion_returns_409(
    job_repository: InMemoryJobRepository,
) -> None:
    slow_client = _make_fake_github_client()
    async for client in _make_client(slow_client, job_repository):
        # Ask for the report before the (synchronously-run-in-tests) background task even
        # has a chance to run, by inspecting a freshly created — still "pending" — job.
        create_response = await client.post(
            "/analyze", json={"username": "octocat", "career_goal": "Backend"}
        )
        job_id = create_response.json()["job_id"]
        pending_job = await job_repository.get(job_id)
        assert pending_job is not None
        pending_job.status = "pending"
        pending_job.result = None
        await job_repository.save(pending_job)

        response = await client.get(f"/analyze/{job_id}/report.pdf")

        assert response.status_code == 409


async def test_unknown_job_id_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/analyze/does-not-exist/status")

    assert response.status_code == 404


async def test_invalid_request_body_returns_422(client: httpx.AsyncClient) -> None:
    response = await client.post("/analyze", json={"username": "octocat"})

    assert response.status_code == 422


async def test_failed_job_reports_error_and_no_result(
    job_repository: InMemoryJobRepository,
) -> None:
    failing_client = _make_fake_github_client(fail_on_list_repos=True)
    async for client in _make_client(failing_client, job_repository):
        create_response = await client.post(
            "/analyze", json={"username": "octocat", "career_goal": "Backend"}
        )
        job_id = create_response.json()["job_id"]

        status_response = await client.get(f"/analyze/{job_id}/status")
        body = status_response.json()

        assert body["status"] == "failed"
        assert body["result"] is None
        assert "boom" in body["error"]
