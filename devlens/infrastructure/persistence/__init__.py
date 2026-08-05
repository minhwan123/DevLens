from devlens.infrastructure.persistence.cache_repository import CacheRepository
from devlens.infrastructure.persistence.in_memory_cache_repository import InMemoryCacheRepository
from devlens.infrastructure.persistence.in_memory_snapshot_repository import (
    InMemorySnapshotRepository,
)
from devlens.infrastructure.persistence.snapshot_repository import SnapshotRepository
from devlens.infrastructure.persistence.sqlite_snapshot_repository import SqliteSnapshotRepository

__all__ = [
    "CacheRepository",
    "InMemoryCacheRepository",
    "InMemorySnapshotRepository",
    "SnapshotRepository",
    "SqliteSnapshotRepository",
]

# JobRepository / InMemoryJobRepository are intentionally NOT re-exported here: they depend on
# devlens.application.jobs, and infrastructure.github.client depends on this package (for
# CacheRepository) while devlens.application depends on infrastructure.github — re-exporting
# job types here would make importing *anything* from this package pull in `application`,
# closing that loop into a circular import. Import them directly:
#   from devlens.infrastructure.persistence.job_repository import JobRepository
#   from devlens.infrastructure.persistence.in_memory_job_repository import InMemoryJobRepository
