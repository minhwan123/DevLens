from unittest.mock import patch

from devlens.application.generate_career_report import GenerateCareerReportUseCase
from devlens.config.settings import Settings
from devlens.infrastructure.github.client import GitHubClient
from devlens.infrastructure.llm.null_commentary_service import NullCommentaryService
from devlens.infrastructure.persistence.in_memory_cache_repository import InMemoryCacheRepository
from devlens.infrastructure.persistence.in_memory_job_repository import InMemoryJobRepository
from devlens.infrastructure.persistence.in_memory_snapshot_repository import (
    InMemorySnapshotRepository,
)
from devlens.interface.api.dependencies import (
    get_cache_repository,
    get_commentary_service,
    get_generate_career_report_use_case,
    get_github_client,
    get_job_repository,
    get_similarity_service,
    get_snapshot_repository,
)


def test_get_cache_repository_is_a_process_wide_singleton() -> None:
    get_cache_repository.cache_clear()

    first = get_cache_repository()
    second = get_cache_repository()

    assert first is second
    assert isinstance(first, InMemoryCacheRepository)


def test_get_job_repository_is_a_process_wide_singleton() -> None:
    get_job_repository.cache_clear()

    first = get_job_repository()
    second = get_job_repository()

    assert first is second
    assert isinstance(first, InMemoryJobRepository)


def test_get_github_client_builds_a_client_from_settings_and_cache() -> None:
    settings = Settings(github_token="secret")

    client = get_github_client(settings, InMemoryCacheRepository())

    assert isinstance(client, GitHubClient)


def test_get_commentary_service_falls_back_to_null_service_without_a_key() -> None:
    settings = Settings(gemini_api_key=None)

    service = get_commentary_service(settings, InMemoryCacheRepository())

    assert isinstance(service, NullCommentaryService)


def test_get_similarity_service_is_a_process_wide_singleton() -> None:
    get_similarity_service.cache_clear()

    with patch("devlens.interface.api.dependencies.EmbeddingSimilarityService") as mock_cls:
        first = get_similarity_service()
        second = get_similarity_service()

    assert first is second
    mock_cls.assert_called_once()


def test_get_snapshot_repository_is_a_process_wide_singleton() -> None:
    get_snapshot_repository.cache_clear()

    with patch("devlens.interface.api.dependencies.SqliteSnapshotRepository") as mock_cls:
        first = get_snapshot_repository()
        second = get_snapshot_repository()

    assert first is second
    mock_cls.assert_called_once()


def test_get_generate_career_report_use_case_composes_its_dependencies() -> None:
    settings = Settings(github_token=None, gemini_api_key=None)
    github_client = get_github_client(settings, InMemoryCacheRepository())
    commentary_service = get_commentary_service(settings, InMemoryCacheRepository())

    use_case = get_generate_career_report_use_case(
        github_client=github_client,
        similarity_service=object(),  # type: ignore[arg-type]  # stored, never called here
        commentary_service=commentary_service,
        snapshot_repository=InMemorySnapshotRepository(),
    )

    assert isinstance(use_case, GenerateCareerReportUseCase)
