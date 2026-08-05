from devlens.application.jobs import Job
from devlens.infrastructure.persistence.job_repository import JobRepository


class InMemoryJobRepository(JobRepository):
    """Process-local job store. Loses state on restart — fine until a real DB-backed
    JobRepository replaces it; every other component only depends on the JobRepository port."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    async def save(self, job: Job) -> None:
        self._jobs[job.job_id] = job

    async def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)
