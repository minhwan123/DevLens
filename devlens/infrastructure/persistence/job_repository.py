from abc import ABC, abstractmethod

from devlens.application.jobs import Job


class JobRepository(ABC):
    """Async job storage port. Swap for a PostgreSQL-backed implementation once DB infra
    exists — see CacheRepository for the same pattern already applied to GitHub caching."""

    @abstractmethod
    async def save(self, job: Job) -> None: ...

    @abstractmethod
    async def get(self, job_id: str) -> Job | None: ...
