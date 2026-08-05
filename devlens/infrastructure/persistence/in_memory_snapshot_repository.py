from devlens.domain.models.radar_snapshot import RadarSnapshot
from devlens.infrastructure.persistence.snapshot_repository import SnapshotRepository


class InMemorySnapshotRepository(SnapshotRepository):
    """Process-local snapshot store, for tests — mirrors InMemoryJobRepository's pattern."""

    def __init__(self) -> None:
        self._snapshots: dict[str, list[RadarSnapshot]] = {}

    async def save(self, username: str, snapshot: RadarSnapshot) -> None:
        self._snapshots.setdefault(username, []).append(snapshot)

    async def list_for_username(self, username: str) -> list[RadarSnapshot]:
        return list(self._snapshots.get(username, []))
