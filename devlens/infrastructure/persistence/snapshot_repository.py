from abc import ABC, abstractmethod

from devlens.domain.models.radar_snapshot import RadarSnapshot


class SnapshotRepository(ABC):
    """Async radar-history storage port, keyed by GitHub username. Unlike JobRepository/
    CacheRepository (deliberately in-memory, per-process), this one is backed by SQLite by
    default so score trends survive a restart — see SqliteSnapshotRepository."""

    @abstractmethod
    async def save(self, username: str, snapshot: RadarSnapshot) -> None: ...

    @abstractmethod
    async def list_for_username(self, username: str) -> list[RadarSnapshot]: ...
