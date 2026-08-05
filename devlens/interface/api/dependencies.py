from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from devlens.application.generate_career_report import (
    GenerateCareerReportUseCase,
    LlmCommentaryPort,
)
from devlens.config.settings import Settings, get_settings
from devlens.infrastructure.github import GitHubClient, build_github_client
from devlens.infrastructure.llm import build_commentary_service
from devlens.infrastructure.persistence import CacheRepository, InMemoryCacheRepository
from devlens.infrastructure.persistence.in_memory_job_repository import InMemoryJobRepository
from devlens.infrastructure.persistence.job_repository import JobRepository
from devlens.infrastructure.persistence.snapshot_repository import SnapshotRepository
from devlens.infrastructure.persistence.sqlite_snapshot_repository import SqliteSnapshotRepository
from devlens.infrastructure.vector_store import EmbeddingSimilarityService


@lru_cache
def get_cache_repository() -> CacheRepository:
    """Process-wide singleton so GitHub and Gemini response caching persists across requests."""
    return InMemoryCacheRepository()


def get_github_client(
    settings: Annotated[Settings, Depends(get_settings)],
    cache: Annotated[CacheRepository, Depends(get_cache_repository)],
) -> GitHubClient:
    return build_github_client(settings, cache)


@lru_cache
def get_similarity_service() -> EmbeddingSimilarityService:
    """Process-wide singleton: loading the Sentence Transformers model is expensive."""
    return EmbeddingSimilarityService()


@lru_cache
def get_job_repository() -> JobRepository:
    """Process-wide singleton so job status survives across the poll requests that read it."""
    return InMemoryJobRepository()


def get_commentary_service(
    settings: Annotated[Settings, Depends(get_settings)],
    cache: Annotated[CacheRepository, Depends(get_cache_repository)],
) -> LlmCommentaryPort:
    """Falls back to a placeholder-text service when GEMINI_API_KEY isn't configured."""
    return build_commentary_service(settings, cache)


@lru_cache
def get_snapshot_repository() -> SnapshotRepository:
    """Process-wide singleton; the underlying SQLite file persists radar history across
    restarts, unlike CacheRepository/JobRepository which are deliberately in-memory only."""
    settings = get_settings()
    return SqliteSnapshotRepository(settings.snapshot_db_path)


def get_generate_career_report_use_case(
    github_client: Annotated[GitHubClient, Depends(get_github_client)],
    similarity_service: Annotated[EmbeddingSimilarityService, Depends(get_similarity_service)],
    commentary_service: Annotated[LlmCommentaryPort, Depends(get_commentary_service)],
    snapshot_repository: Annotated[SnapshotRepository, Depends(get_snapshot_repository)],
) -> GenerateCareerReportUseCase:
    return GenerateCareerReportUseCase(
        github_client=github_client,
        similarity_service=similarity_service,
        commentary_service=commentary_service,
        snapshot_repository=snapshot_repository,
    )
